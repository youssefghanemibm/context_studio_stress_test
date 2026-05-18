package com.corvane.chub.claimcore;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Claim aggregate API. Claim references have the form CLM-&lt;region&gt;-&lt;yyyy&gt;-&lt;6 digits&gt;;
 * migrated claims keep their CLARA CLAIM_ID in claim_core.claim.legacy_claim_id.
 */
@RestController
@RequestMapping("/claims")
public class ClaimController {

    private final ClaimService claims;

    public ClaimController(ClaimService claims) {
        this.claims = claims;
    }

    @GetMapping("/{claimId}")
    public ResponseEntity<ClaimView> get(@PathVariable String claimId) {
        return claims.find(claimId).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<ClaimView> create(@RequestBody CreateClaimFromFnol request) {
        return ResponseEntity.status(201).body(claims.createFromFnol(request));
    }

    @PatchMapping("/{claimId}")
    public ResponseEntity<ClaimView> update(@PathVariable String claimId, @RequestBody ClaimPatch patch) {
        return ResponseEntity.ok(claims.update(claimId, patch));
    }
}
