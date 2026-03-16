package com.corvane.chub.fraud;

import java.time.LocalDate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * Records or defers the customer notice for a referral. The deadline is the referral date
 * plus 10 business days (BR-FRD-032); a deferral needs SIU certification of a tipping-off
 * risk (BR-FRD-036).
 */
@RestController
public class CustomerNoticeController {

    private final CustomerNoticeService notices;

    public CustomerNoticeController(CustomerNoticeService notices) {
        this.notices = notices;
    }

    @PostMapping("/referrals/{referralId}/customer-notice")
    public ResponseEntity<CustomerNoticeService.Notice> recordOrDefer(@PathVariable String referralId,
                                                                      @RequestBody NoticeRequest request) {
        return ResponseEntity.ok(notices.recordOrDefer(referralId, request.action(), request.deferUntil(),
                request.certifiedBy()));
    }

    public record NoticeRequest(String action, LocalDate deferUntil, String certifiedBy) {
    }
}
