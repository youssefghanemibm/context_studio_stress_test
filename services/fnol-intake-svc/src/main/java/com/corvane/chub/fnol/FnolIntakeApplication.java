package com.corvane.chub.fnol;

import java.util.List;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * Entry point for fnol-intake-svc.
 */
@SpringBootApplication
@ConfigurationPropertiesScan
public class FnolIntakeApplication {

    public static void main(String[] args) {
        SpringApplication.run(FnolIntakeApplication.class, args);
    }

    /** Topics this service consumes and produces, bound from {@code chub.kafka.*}. */
    @ConfigurationProperties(prefix = "chub.kafka")
    public record KafkaTopics(String cluster, List<String> consumes, List<String> produces) {
    }
}
