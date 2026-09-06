package com.flexiple.sourcing;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class ProfileRepository {
    private final List<Models.Profile> profiles;

    public ProfileRepository(ObjectMapper mapper) {
        try (InputStream in = new ClassPathResource("profiles.json").getInputStream()) {
            // The assignment data is copied to src/main/resources so the app is self-contained.
            this.profiles = List.copyOf(mapper.readValue(in, new TypeReference<List<Models.Profile>>() {}));
        } catch (Exception e) {
            throw new IllegalStateException("Could not load profiles.json", e);
        }
    }

    public List<Models.Profile> filter(Models.Filters filters) {
        return profiles.stream()
                .filter(p -> matchesSkills(p, filters.skills()))
                .filter(p -> filters.minYearsExperience() == null || p.years_experience() >= filters.minYearsExperience())
                .filter(p -> filters.maxYearsExperience() == null || p.years_experience() <= filters.maxYearsExperience())
                .filter(p -> filters.location() == null || filters.location().isBlank()
                        || normal(p.location()).equals(normal(filters.location())))
                .filter(p -> matchesCompanyTypes(p, filters.companyTypes()))
                .toList();
    }

    private boolean matchesSkills(Models.Profile p, List<String> required) {
        if (required == null || required.isEmpty()) return true;
        List<String> candidateSkills = p.skills().stream().map(this::normal).toList();
        return required.stream().map(this::normal).allMatch(req -> skillMatches(req, candidateSkills));
    }

    /**
     * Exact match first, then alias expansion and substring containment so
     * "RDS" matches "AWS RDS" and "postgres" matches "PostgreSQL".
     */
    private boolean skillMatches(String required, List<String> candidateSkills) {
        if (candidateSkills.contains(required)) return true;

        Set<String> aliases = skillAliases(required);
        for (String candidate : candidateSkills) {
            if (aliases.contains(candidate)) return true;
            if (candidate.contains(required) || required.contains(candidate)) return true;
            for (String alias : aliases) {
                if (candidate.contains(alias) || alias.contains(candidate)) return true;
            }
        }
        return false;
    }

    private Set<String> skillAliases(String skill) {
        Set<String> out = new LinkedHashSet<>();
        out.add(skill);
        switch (skill) {
            case "rds", "aws rds" -> { out.add("rds"); out.add("aws rds"); out.add("aws"); }
            case "postgres", "postgresql", "psql" -> { out.add("postgres"); out.add("postgresql"); }
            case "js", "javascript", "node", "nodejs", "node.js" -> {
                out.add("javascript"); out.add("node.js"); out.add("nodejs"); out.add("node");
            }
            case "ts", "typescript" -> out.add("typescript");
            case "k8s", "kubernetes" -> { out.add("k8s"); out.add("kubernetes"); }
            case "py", "python" -> out.add("python");
            case "react.js", "reactjs", "react" -> out.add("react");
            case "next", "nextjs", "next.js" -> out.add("next.js");
            case "mongo", "mongodb" -> out.add("mongodb");
            case "tf", "terraform" -> out.add("terraform");
            default -> { }
        }
        return out;
    }

    private boolean matchesCompanyTypes(Models.Profile p, List<String> required) {
        if (required == null || required.isEmpty()) return true;
        Set<String> types = new HashSet<>();
        if (p.current_company_type() != null) types.add(normal(p.current_company_type()));
        if (p.past_companies() != null) {
            p.past_companies().forEach(c -> {
                if (c.company_type() != null) types.add(normal(c.company_type()));
            });
        }
        // UI labels this as "any" — candidate matches if they have experience at any selected type.
        return required.stream().map(this::normal).anyMatch(types::contains);
    }

    private String normal(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    public Optional<Models.Profile> findById(String id) {
        return profiles.stream().filter(p -> p.id().equals(id)).findFirst();
    }

    public List<String> knownSkills() {
        return profiles.stream()
                .flatMap(p -> p.skills().stream())
                .distinct()
                .sorted(String.CASE_INSENSITIVE_ORDER)
                .toList();
    }

    public int size() { return profiles.size(); }
}
