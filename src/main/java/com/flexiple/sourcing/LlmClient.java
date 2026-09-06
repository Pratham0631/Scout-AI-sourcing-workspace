package com.flexiple.sourcing;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

@Component
public class LlmClient {
    private final ObjectMapper mapper;
    private final HttpClient client;
    private final String apiKey;
    private final String baseUrl;
    private final String model;

    public LlmClient(ObjectMapper mapper,
                     @Value("${OPENROUTER_API_KEY:}") String apiKey,
                     @Value("${LLM_BASE_URL:https://openrouter.ai/api/v1}") String baseUrl,
                     @Value("${LLM_MODEL:google/gemini-2.5-flash}") String model) {
        this.mapper = mapper;
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.model = model;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(8))
                .build();
    }

    public JsonNode complete(String systemPrompt, String userPrompt) {
        if (apiKey == null || apiKey.isBlank()) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,
                    "LLM API key is not configured. Set OPENROUTER_API_KEY and restart the app.");
        }

        Map<String, Object> body = Map.of(
                "model", model,
                "temperature", 0.1,
                "max_tokens", 8000,
                "messages", new Object[]{
                        Map.of("role", "system", "content", systemPrompt),
                        Map.of("role", "user", "content", userPrompt)
                },
                "response_format", Map.of("type", "json_object")
        );

        String json;
        try {
            json = mapper.writeValueAsString(body);
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Could not build LLM request.");
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl.replaceAll("/$", "") + "/chat/completions"))
                .timeout(Duration.ofSeconds(45))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .header("HTTP-Referer", "http://localhost:8080")
                .header("X-Title", "Flexiple Sourcing Refinement Loop")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        try {
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 429) {
                throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS,
                        "The LLM provider rate-limited this request. Please wait a moment and retry.");
            }
            if (response.statusCode() >= 500) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM provider is temporarily unavailable. Please retry.");
            }
            if (response.statusCode() == 402) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM provider needs more credits for this request. Add credits or lower max_tokens.");
            }
            if (response.statusCode() >= 400) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM request was rejected. Check the API key, model and provider settings.");
            }

            JsonNode root = mapper.readTree(response.body());
            JsonNode content = root.path("choices").path(0).path("message").path("content");
            if (!content.isTextual()) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM returned an unexpected response shape.");
            }
            return parseJsonObject(content.asText());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ResponseStatusException(HttpStatus.GATEWAY_TIMEOUT,
                    "The LLM request was interrupted. Please retry.");
        } catch (java.io.IOException e) {
            throw new ResponseStatusException(HttpStatus.GATEWAY_TIMEOUT,
                    "The LLM request timed out or could not be reached. Please retry.");
        }
    }

    private JsonNode parseJsonObject(String content) {
        String cleaned = content.trim();
        if (cleaned.startsWith("```")) {
            cleaned = cleaned.replaceFirst("^```(?:json)?\\s*", "")
                    .replaceFirst("\\s*```$", "");
        }
        try {
            JsonNode node = mapper.readTree(cleaned);
            if (node == null || !node.isObject()) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM returned malformed structured output.");
            }
            return node;
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                    "The LLM returned malformed JSON. Please retry.");
        }
    }
}
