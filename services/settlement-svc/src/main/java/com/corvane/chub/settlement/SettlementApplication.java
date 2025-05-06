package com.corvane.chub.settlement;

import java.util.List;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

/**
 * Entry point for settlement-svc.
 */
@SpringBootApplication
@ConfigurationPropertiesScan
public class SettlementApplication {

    public static void main(String[] args) {
        SpringApplication.run(SettlementApplication.class, args);
    }

    /** Topics this service consumes and produces, bound from {@code chub.kafka.*}. */
    @ConfigurationProperties(prefix = "chub.kafka")
    public record KafkaTopics(String cluster, List<String> consumes, List<String> produces) {
    }
}
