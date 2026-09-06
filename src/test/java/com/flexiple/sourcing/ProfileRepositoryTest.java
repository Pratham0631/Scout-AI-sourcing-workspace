package com.flexiple.sourcing;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ProfileRepositoryTest {
    @Test
    void loadsAllSuppliedProfiles() {
        ProfileRepository repository = new ProfileRepository(new ObjectMapper());
        assertEquals(48, repository.size());
    }

    @Test
    void appliesObjectiveFiltersLocally() {
        ProfileRepository repository = new ProfileRepository(new ObjectMapper());
        var filters = new Models.Filters(
                List.of("AWS RDS"),
                4, 7, "Bangalore", List.of("startup")
        );
        var results = repository.filter(filters);
        assertFalse(results.isEmpty());
        assertTrue(results.stream().allMatch(p -> p.years_experience() >= 4 && p.years_experience() <= 7));
        assertTrue(results.stream().allMatch(p -> p.location().equalsIgnoreCase("Bangalore")));
    }

    @Test
    void matchesSkillAliasesLikeRds() {
        ProfileRepository repository = new ProfileRepository(new ObjectMapper());
        var filters = new Models.Filters(List.of("RDS"), 4, 7, "Bangalore", List.of("startup"));
        assertFalse(repository.filter(filters).isEmpty());
    }

    @Test
    void companyTypesMatchAnySelectedType() {
        ProfileRepository repository = new ProfileRepository(new ObjectMapper());
        var filters = new Models.Filters(List.of(), null, null, null, List.of("startup", "agency"));
        var results = repository.filter(filters);
        assertFalse(results.isEmpty());
        assertTrue(results.stream().allMatch(p -> {
            java.util.Set<String> types = new java.util.HashSet<>();
            if (p.current_company_type() != null) types.add(p.current_company_type().toLowerCase());
            if (p.past_companies() != null) {
                p.past_companies().forEach(c -> {
                    if (c.company_type() != null) types.add(c.company_type().toLowerCase());
                });
            }
            return types.contains("startup") || types.contains("agency");
        }));
    }
}
