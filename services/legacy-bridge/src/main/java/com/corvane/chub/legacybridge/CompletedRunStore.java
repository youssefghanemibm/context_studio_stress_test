package com.corvane.chub.legacybridge;

import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.stereotype.Component;

@Component
public class CompletedRunStore {

    private final List<ExtractRun> runs = new CopyOnWriteArrayList<>();

    public void add(ExtractRun run) {
        runs.add(run);
    }

    public List<ExtractRun> since(String interfaceId, LocalDateTime since) {
        return runs.stream()
                .filter(r -> r.interfaceId().equals(interfaceId) && r.runTs().isAfter(since))
                .toList();
    }
}
