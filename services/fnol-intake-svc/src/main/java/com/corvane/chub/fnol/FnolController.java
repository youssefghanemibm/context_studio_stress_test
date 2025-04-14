package com.corvane.chub.fnol;

import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * First Notice of Loss intake. Every accepted FNOL is stored in fnol.notification and
 * published as fnol.received.v1 for triage-svc, claim-core-svc and notification-svc.
 */
@RestController
public class FnolController {

    private final FnolService fnol;

    public FnolController(FnolService fnol) {
        this.fnol = fnol;
    }

    @PostMapping("/fnol")
    public ResponseEntity<FnolReceipt> submit(@RequestBody FnolRequest request) {
        return ResponseEntity.accepted().body(fnol.accept(request));
    }

    @GetMapping("/fnol/{fnolId}")
    public ResponseEntity<FnolStatus> status(@PathVariable UUID fnolId) {
        return fnol.status(fnolId).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }
}
