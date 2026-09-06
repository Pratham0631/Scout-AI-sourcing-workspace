package com.flexiple.sourcing;

import java.util.List;

public final class Models {
    private Models() {}

    public record Filters(
            List<String> skills,
            Integer minYearsExperience,
            Integer maxYearsExperience,
            String location,
            List<String> companyTypes
    ) {
        public Filters {
            skills = skills == null ? List.of() : List.copyOf(skills);
            companyTypes = companyTypes == null ? List.of() : List.copyOf(companyTypes);
        }
    }

    public record Rubric(
            List<RubricCriterion> criteria
    ) {
        public Rubric {
            criteria = criteria == null ? List.of() : List.copyOf(criteria);
        }
    }

    public record RubricCriterion(
            String name,
            String description,
            Integer weight
    ) {}

    public record PastCompany(
            String company,
            String company_type,
            String title,
            Integer years
    ) {}

    public record Profile(
            String id,
            String name,
            String current_title,
            Integer years_experience,
            String location,
            String current_company,
            String current_company_type,
            List<String> skills,
            List<PastCompany> past_companies,
            String education,
            String summary
    ) {}

    public record ScoreResult(
            String profileId,
            Integer score,
            String explanation,
            List<String> evidence
    ) {}

    public record RankedProfile(
            Profile profile,
            Integer score,
            String explanation,
            List<String> evidence
    ) {}

    public record SearchResponse(
            String sessionId,
            String status,
            Filters filters,
            Rubric rubric,
            List<RankedProfile> results,
            int filteredCount,
            List<String> warnings,
            String error
    ) {}

    public record RefinementResponse(
            String sessionId,
            String status,
            Filters filters,
            Rubric rubric,
            List<RankedProfile> results,
            int filteredCount,
            List<RefinementChange> changes,
            List<String> warnings,
            String error
    ) {}

    public record RefinementChange(
            String field,
            String before,
            String after,
            String reason
    ) {}

    public record RefineRequest(
            Filters filters,
            Rubric rubric,
            List<RankedProfile> shownProfiles,
            String feedback
    ) {}

    public record FreezeResponse(
            String sessionId,
            String status,
            Filters filters,
            Rubric rubric,
            List<RankedProfile> finalShortlist
    ) {}
}
