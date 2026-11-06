package com.corvane.chub.legacybridge;

import java.time.LocalDateTime;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ExtractRunController {

    private final CompletedRunStore store;

    public ExtractRunController(CompletedRunStore store) {
        this.store = store;
    }

    @GetMapping("/extract-runs")
    public List<ExtractRun> completed(@RequestParam("interface") String interfaceId,
                                      @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                                      LocalDateTime since) {
        return store.since(interfaceId, since);
    }
}
