package com.flexiple.sourcing;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class SourcingController {
    private final SourcingService service;
    private final SessionStore sessions;

    public SourcingController(SourcingService service, SessionStore sessions) {
        this.service = service;
        this.sessions = sessions;
    }

    @PostMapping("/search")
    public Models.SearchResponse search(@RequestBody SearchRequest request) {
        String id = UUID.randomUUID().toString();
        Models.SearchResponse response = service.start(request.query(), id);
        sessions.create(response);
        return response;
    }

    @PostMapping("/sessions/{id}/refine")
    public Models.RefinementResponse refine(@PathVariable String id, @RequestBody Models.RefineRequest request) {
        SessionStore.State state = sessions.get(id);
        if (state.frozen) throw new org.springframework.web.server.ResponseStatusException(
                org.springframework.http.HttpStatus.CONFLICT, "This search is frozen.");
        Models.RefineRequest serverRequest = new Models.RefineRequest(
                state.filters, state.rubric, request.shownProfiles(), request.feedback());
        Models.RefinementResponse response = service.refine(id, serverRequest);
        state.filters = response.filters();
        state.rubric = response.rubric();
        state.results = response.results();
        state.filteredCount = response.filteredCount();
        return response;
    }

    @PostMapping("/sessions/{id}/edit")
    public Models.RefinementResponse edit(@PathVariable String id, @RequestBody EditRequest request) {
        SessionStore.State state = sessions.get(id);
        if (state.frozen) throw new org.springframework.web.server.ResponseStatusException(
                org.springframework.http.HttpStatus.CONFLICT, "This search is frozen.");

        Models.SearchResponse response = service.applyEdits(id, request.filters(), request.rubric());
        state.filters = response.filters();
        state.rubric = response.rubric();
        state.results = response.results();
        state.filteredCount = response.filteredCount();

        return new Models.RefinementResponse(id, response.status(), response.filters(), response.rubric(),
                response.results(), response.filteredCount(), List.of(), response.warnings(), response.error());
    }

    @PostMapping("/sessions/{id}/freeze")
    public Models.FreezeResponse freeze(@PathVariable String id) {
        SessionStore.State state = sessions.get(id);
        state.frozen = true;
        return new Models.FreezeResponse(id, "frozen", state.filters, state.rubric, state.results);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("ok");
    }

    public record SearchRequest(String query) {}
    public record EditRequest(Models.Filters filters, Models.Rubric rubric) {}
}
