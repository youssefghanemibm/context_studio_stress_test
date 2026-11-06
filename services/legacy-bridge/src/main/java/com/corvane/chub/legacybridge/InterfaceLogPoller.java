package com.corvane.chub.legacybridge;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** Reads the CLARA interface log on the configured interval and remembers completed runs. */
@Component
public class InterfaceLogPoller {

    private final ExtractRunRepository repository;
    private final BridgeProperties properties;
    private final CompletedRunStore store;
    private final Map<String, LocalDateTime> highWater = new ConcurrentHashMap<>();

    public InterfaceLogPoller(ExtractRunRepository repository, BridgeProperties properties,
                              CompletedRunStore store) {
        this.repository = repository;
        this.properties = properties;
        this.store = store;
    }

    @Scheduled(fixedDelayString = "${bridge.poll-interval}")
    public void poll() {
        for (String interfaceId : properties.interfaces()) {
            LocalDateTime since = highWater.getOrDefault(interfaceId, LocalDateTime.now().minusDays(1));
            for (ExtractRun run : repository.runsSince(interfaceId, since)) {
                if (run.completed()) {
                    store.add(run);
                }
                highWater.put(interfaceId, run.runTs());
            }
        }
    }
}
