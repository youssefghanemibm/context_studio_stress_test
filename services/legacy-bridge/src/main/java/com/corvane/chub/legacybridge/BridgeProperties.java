package com.corvane.chub.legacybridge;

import java.time.Duration;
import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

/** Bound from {@code bridge.*}; the poll interval is set per environment. */
@ConfigurationProperties(prefix = "bridge")
public record BridgeProperties(Duration pollInterval, List<String> interfaces) {
}
