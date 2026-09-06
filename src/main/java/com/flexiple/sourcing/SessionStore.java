package com.flexiple.sourcing;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SessionStore {
    public static class State {
        public Models.Filters filters;
        public Models.Rubric rubric;
        public java.util.List<Models.RankedProfile> results;
        public int filteredCount;
        public boolean frozen;

        public State(Models.Filters filters, Models.Rubric rubric,
                     java.util.List<Models.RankedProfile> results, int filteredCount) {
            this.filters = filters;
            this.rubric = rubric;
            this.results = results;
            this.filteredCount = filteredCount;
        }
    }

    private final Map<String, State> sessions = new ConcurrentHashMap<>();

    public String create(Models.SearchResponse response) {
        String id = response.sessionId() == null ? UUID.randomUUID().toString() : response.sessionId();
        sessions.put(id, new State(response.filters(), response.rubric(), response.results(), response.filteredCount()));
        return id;
    }

    public State get(String id) {
        State state = sessions.get(id);
        if (state == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Search session not found.");
        }
        return state;
    }
}
