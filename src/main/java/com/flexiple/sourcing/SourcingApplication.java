package com.flexiple.sourcing;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SourcingApplication {
    public static void main(String[] args) {
        EnvLoader.loadDotEnv();
        SpringApplication.run(SourcingApplication.class, args);
    }
}
