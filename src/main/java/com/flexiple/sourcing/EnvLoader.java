package com.flexiple.sourcing;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Loads a local .env file into the process environment for development.
 * Real secrets must live in .env (gitignored) or the OS environment — never in committed files.
 */
final class EnvLoader {
    private EnvLoader() {}

    static void loadDotEnv() {
        Path envFile = Path.of(".env");
        if (!Files.isRegularFile(envFile)) return;

        try {
            List<String> lines = Files.readAllLines(envFile);
            for (String raw : lines) {
                String line = raw.trim();
                if (line.isEmpty() || line.startsWith("#") || !line.contains("=")) continue;
                int eq = line.indexOf('=');
                String key = line.substring(0, eq).trim();
                String value = line.substring(eq + 1).trim();
                if ((value.startsWith("\"") && value.endsWith("\""))
                        || (value.startsWith("'") && value.endsWith("'"))) {
                    value = value.substring(1, value.length() - 1);
                }
                if (key.isEmpty()) continue;
                if (System.getenv(key) == null && System.getProperty(key) == null) {
                    System.setProperty(key, value);
                }
            }
        } catch (IOException ignored) {
            // Missing/unreadable .env is fine; production should use real env vars.
        }
    }
}
