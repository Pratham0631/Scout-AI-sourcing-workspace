package com.flexiple.sourcing;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class SourcingService {
    private final LlmClient llm;
    private final ProfileRepository repository;
    private final ObjectMapper mapper;
    private final String initialPrompt;
    private final String scorePrompt;
    private final String refinePrompt;

    public SourcingService(LlmClient llm, ProfileRepository repository, ObjectMapper mapper) {
        this.llm = llm;
        this.repository = repository;
        this.mapper = mapper;
        this.initialPrompt = loadPrompt("prompts/initial-search.txt");
        this.scorePrompt = loadPrompt("prompts/score-profiles.txt");
        this.refinePrompt = loadPrompt("prompts/refine-search.txt");
    }

    public Models.SearchResponse start(String query, String sessionId) {
        if (query == null || query.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Tell us what kind of candidate you are looking for.");
        }

        JsonNode root = llm.complete(initialPrompt, """
                Recruiter request:
                %s

                Dataset context:
                The candidate pool contains %d fictional profiles. Company types are startup, scaleup, enterprise, agency.
                Prefer skill filter values from this exact vocabulary when possible:
                %s
                """.formatted(query.trim(), repository.size(), String.join(", ", repository.knownSkills())));

        Models.Filters filters = parseFilters(root.path("filters"));
        Models.Rubric rubric = parseRubric(root.path("rubric"));
        return runSearch(sessionId, filters, rubric, List.of());
    }

    public Models.RefinementResponse refine(String sessionId, Models.RefineRequest request) {
        validateRefineRequest(request);

        String shown = request.shownProfiles().stream()
                .map(Models.RankedProfile::profile)
                .map(this::profileJson)
                .collect(Collectors.joining("\n"));

        JsonNode root = llm.complete(refinePrompt, """
                Current filters:
                %s

                Current rubric:
                %s

                Profiles the recruiter just reviewed:
                %s

                Recruiter feedback:
                %s
                """.formatted(
                json(request.filters()),
                json(request.rubric()),
                shown,
                request.feedback().trim()));

        Models.Filters newFilters = parseFilters(root.path("filters"));
        Models.Rubric newRubric = parseRubric(root.path("rubric"));
        List<Models.RefinementChange> changes = parseChanges(root.path("changes"));

        List<Models.RankedProfile> results = runSearch(sessionId, newFilters, newRubric, List.of()).results();

        // Never display a claimed change unless the returned state actually changed.
        changes = changes.stream()
                .filter(c -> !Objects.equals(c.before(), c.after()))
                .toList();

        return new Models.RefinementResponse(
                sessionId, "ready", newFilters, newRubric, results,
                repository.filter(newFilters).size(), changes, List.of(), null);
    }

    private Models.SearchResponse runSearch(String sessionId, Models.Filters filters,
                                            Models.Rubric rubric, List<String> warnings) {
        List<Models.Profile> filtered = repository.filter(filters);
        if (filtered.isEmpty()) {
            return new Models.SearchResponse(sessionId, "empty", filters, rubric,
                    List.of(), 0, warnings, null);
        }

        JsonNode root = llm.complete(scorePrompt, """
                Fit rubric:
                %s

                Candidate profiles:
                %s
                """.formatted(
                json(rubric),
                filtered.stream().map(this::profileJson).collect(Collectors.joining("\n"))));

        List<Models.ScoreResult> scores = parseScores(root.path("scores"), filtered);
        List<Models.RankedProfile> ranked = scores.stream()
                .sorted(Comparator.comparing(Models.ScoreResult::score).reversed())
                .limit(5)
                .map(s -> {
                    Models.Profile p = repository.findById(s.profileId()).orElseThrow();
                    return new Models.RankedProfile(p, s.score(), validateExplanation(s, p), validateEvidence(s, p));
                })
                .toList();

        return new Models.SearchResponse(sessionId, "ready", filters, rubric,
                ranked, filtered.size(), warnings, null);
    }

    private List<Models.ScoreResult> parseScores(JsonNode node, List<Models.Profile> expected) {
        if (!node.isArray() || node.size() != expected.size()) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                    "The LLM returned an incomplete scoring response. Nothing was applied; please retry.");
        }

        Set<String> ids = expected.stream().map(Models.Profile::id).collect(Collectors.toSet());
        Set<String> seen = new HashSet<>();
        List<Models.ScoreResult> out = new ArrayList<>();

        for (JsonNode n : node) {
            String id = textRequired(n, "profileId");
            if (!ids.contains(id) || !seen.add(id)) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM returned invalid candidate IDs. Nothing was applied; please retry.");
            }
            int score = intInRange(n, "score", 0, 100);
            String explanation = textRequired(n, "explanation");
            if (!n.path("evidence").isArray() || n.path("evidence").isEmpty()) {
                throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                        "The LLM did not provide evidence for a candidate. Please retry.");
            }
            List<String> evidence = new ArrayList<>();
            n.path("evidence").forEach(e -> {
                if (!e.isTextual() || e.asText().isBlank()) {
                    throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "Malformed evidence from LLM.");
                }
                evidence.add(e.asText());
            });
            out.add(new Models.ScoreResult(id, score, explanation, evidence));
        }
        return out;
    }

    private Models.Filters parseFilters(JsonNode n) {
        if (!n.isObject()) invalid("Missing filters.");
        List<String> skills = stringArray(n, "skills", 20);
        List<String> companyTypes = stringArray(n, "companyTypes", 4);
        for (String type : companyTypes) {
            if (!Set.of("startup", "scaleup", "enterprise", "agency").contains(type.toLowerCase(Locale.ROOT))) {
                invalid("Invalid company type: " + type);
            }
        }
        Integer min = nullableInt(n, "minYearsExperience");
        Integer max = nullableInt(n, "maxYearsExperience");
        if (min != null && (min < 0 || min > 50)) invalid("Invalid minimum experience.");
        if (max != null && (max < 0 || max > 50)) invalid("Invalid maximum experience.");
        if (min != null && max != null && min > max) invalid("Experience range is invalid.");
        String location = nullableText(n, "location");
        return new Models.Filters(skills, min, max, location, companyTypes);
    }

    private Models.Rubric parseRubric(JsonNode n) {
        if (!n.isObject() || !n.path("criteria").isArray()) invalid("Missing rubric criteria.");
        List<Models.RubricCriterion> criteria = new ArrayList<>();
        int total = 0;
        for (JsonNode c : n.path("criteria")) {
            String name = textRequired(c, "name");
            String description = textRequired(c, "description");
            int weight = intInRange(c, "weight", 1, 100);
            criteria.add(new Models.RubricCriterion(name, description, weight));
            total += weight;
        }
        if (criteria.size() < 3 || criteria.size() > 6 || total != 100) {
            invalid("Rubric must contain 3-6 criteria whose weights sum to 100.");
        }
        return new Models.Rubric(criteria);
    }

    private List<Models.RefinementChange> parseChanges(JsonNode n) {
        if (!n.isArray()) invalid("Missing refinement changes.");
        List<Models.RefinementChange> result = new ArrayList<>();
        for (JsonNode c : n) {
            result.add(new Models.RefinementChange(
                    textRequired(c, "field"),
                    textRequired(c, "before"),
                    textRequired(c, "after"),
                    textRequired(c, "reason")));
        }
        return result;
    }

    private void validateRefineRequest(Models.RefineRequest request) {
        if (request == null || request.filters() == null || request.rubric() == null
                || request.feedback() == null || request.feedback().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Please provide recruiter feedback.");
        }
        if (request.shownProfiles() == null || request.shownProfiles().isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "No reviewed profiles were supplied.");
        }
    }

    private String validateExplanation(Models.ScoreResult score, Models.Profile p) {
        // The model's explanation is accepted only alongside validated evidence.
        // This prevents unsupported candidate claims from becoming the product's source of truth.
        return score.explanation();
    }

    private List<String> validateEvidence(Models.ScoreResult score, Models.Profile p) {
        List<String> valid = new ArrayList<>();
        for (String e : score.evidence()) {
            String normalized = e.toLowerCase(Locale.ROOT);
            if (normalized.contains("skills") || normalized.contains("years_experience")
                    || normalized.contains("location") || normalized.contains("current_company")
                    || normalized.contains("current_company_type") || normalized.contains("current_title")
                    || normalized.contains("summary") || normalized.contains("past_companies")
                    || normalized.contains("education")) {
                boolean grounded = p.skills().stream().anyMatch(v -> normalized.contains(v.toLowerCase(Locale.ROOT)))
                        || normalized.contains(String.valueOf(p.years_experience()))
                        || normalized.contains(p.location().toLowerCase(Locale.ROOT))
                        || normalized.contains(p.current_company().toLowerCase(Locale.ROOT))
                        || normalized.contains(p.current_company_type().toLowerCase(Locale.ROOT))
                        || normalized.contains(p.current_title().toLowerCase(Locale.ROOT))
                        || (p.summary() != null && normalized.contains(p.summary().toLowerCase(Locale.ROOT)))
                        || (p.education() != null && normalized.contains(p.education().toLowerCase(Locale.ROOT)))
                        || (p.past_companies() != null && p.past_companies().stream().anyMatch(c ->
                        (c.company() != null && normalized.contains(c.company().toLowerCase(Locale.ROOT)))
                                || (c.company_type() != null && normalized.contains(c.company_type().toLowerCase(Locale.ROOT)))
                                || (c.title() != null && normalized.contains(c.title().toLowerCase(Locale.ROOT)))));
                if (grounded) valid.add(e);
            }
        }
        if (valid.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                    "The LLM returned evidence that could not be verified against the candidate profile.");
        }
        return valid;
    }

    private String profileJson(Models.Profile p) {
        return json(p);
    }

    private String json(Object value) {
        try { return mapper.writeValueAsString(value); }
        catch (Exception e) { throw new IllegalStateException(e); }
    }

    private String loadPrompt(String path) {
        try (var in = new ClassPathResource(path).getInputStream()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("Prompt not found: " + path, e);
        }
    }

    private List<String> stringArray(JsonNode parent, String field, int max) {
        JsonNode n = parent.path(field);
        if (!n.isArray() || n.size() > max) invalid("Invalid " + field + ".");
        List<String> values = new ArrayList<>();
        n.forEach(v -> {
            if (!v.isTextual() || v.asText().isBlank()) invalid("Invalid " + field + " value.");
            values.add(v.asText().trim());
        });
        return values;
    }

    private Integer nullableInt(JsonNode n, String field) {
        JsonNode value = n.path(field);
        if (value.isNull() || value.isMissingNode()) return null;
        if (!value.isIntegralNumber()) invalid("Invalid " + field + ".");
        return value.asInt();
    }

    private String nullableText(JsonNode n, String field) {
        JsonNode value = n.path(field);
        if (value.isNull() || value.isMissingNode()) return null;
        if (!value.isTextual()) invalid("Invalid " + field + ".");
        return value.asText().trim();
    }

    private String textRequired(JsonNode n, String field) {
        JsonNode v = n.path(field);
        if (!v.isTextual() || v.asText().isBlank()) invalid("Missing " + field + ".");
        return v.asText().trim();
    }

    private int intInRange(JsonNode n, String field, int min, int max) {
        JsonNode v = n.path(field);
        if (!v.isIntegralNumber() || v.asInt() < min || v.asInt() > max) invalid("Invalid " + field + ".");
        return v.asInt();
    }

    private void invalid(String message) {
        throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
                "The LLM returned invalid structured data: " + message);
    }

    public Models.SearchResponse applyEdits(String sessionId, Models.Filters filters, Models.Rubric rubric) {
        validateFilters(filters);
        validateRubricObject(rubric);
        return runSearch(sessionId, filters, rubric, List.of("Filters/rubric were edited by the recruiter."));
    }

    private void validateFilters(Models.Filters f) {
        if (f == null) badRequest("Filters are required.");
        if (f.minYearsExperience() != null && (f.minYearsExperience() < 0 || f.minYearsExperience() > 50)) {
            badRequest("Invalid minimum experience.");
        }
        if (f.maxYearsExperience() != null && (f.maxYearsExperience() < 0 || f.maxYearsExperience() > 50)) {
            badRequest("Invalid maximum experience.");
        }
        if (f.minYearsExperience() != null && f.maxYearsExperience() != null
                && f.minYearsExperience() > f.maxYearsExperience()) {
            badRequest("Experience range is invalid.");
        }
    }

    private void validateRubricObject(Models.Rubric r) {
        if (r == null || r.criteria() == null || r.criteria().size() < 3 || r.criteria().size() > 6
                || r.criteria().stream().anyMatch(c -> c == null || c.name() == null || c.description() == null
                || c.weight() == null || c.weight() < 1 || c.weight() > 100)
                || r.criteria().stream().mapToInt(Models.RubricCriterion::weight).sum() != 100) {
            badRequest("Rubric must contain 3-6 criteria whose weights sum to 100.");
        }
    }

    private void badRequest(String message) {
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
