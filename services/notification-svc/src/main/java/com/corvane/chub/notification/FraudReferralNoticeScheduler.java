package com.corvane.chub.notification;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Schedules the customer notice that follows a fraud referral (BR-FRD-032 v2, NISA Circular
 * 2026/04 section 3.2).
 *
 * <p>fraud-referral-svc publishes {@code fraud.referral.notice-due.v1} when a referral is
 * created. This class works out the latest date the written notice may go out: the referral
 * date plus ten business days, skipping weekends and the public holidays of the claim's
 * region. A deferral approved under BR-FRD-036 arrives as a later event and moves the date.
 * Letters use Notify template FRN01 and SMS uses FRN02 (ADR-014).
 */
@Component
public class FraudReferralNoticeScheduler {

    /** BR-FRD-032 v2: notice within 10 business days of the referral. */
    static final int NOTICE_BUSINESS_DAYS = 10;

    /** Holiday calendars used for business-day arithmetic. */
    static final List<String> CALENDAR_REGIONS = List.of("UK", "NO", "SE", "DK");

    private final Map<String, HolidayCalendar> calendars;
    private final NoticeQueue queue;

    public FraudReferralNoticeScheduler(Map<String, HolidayCalendar> calendars, NoticeQueue queue) {
        for (String region : CALENDAR_REGIONS) {
            if (!calendars.containsKey(region)) {
                throw new IllegalStateException("No holiday calendar for region " + region);
            }
        }
        this.calendars = calendars;
        this.queue = queue;
    }

    @KafkaListener(topics = "fraud.referral.notice-due.v1", groupId = "notification-svc")
    public void onNoticeDue(NoticeDueEvent event) {
        LocalDate due = dueDate(event.referralDate(), event.region());
        queue.schedule(event.referralId(), event.claimId(), due, event.deferredUntil());
    }

    /** Referral date plus {@value #NOTICE_BUSINESS_DAYS} business days in the claim's region. */
    public LocalDate dueDate(LocalDate referralDate, String region) {
        HolidayCalendar calendar = calendars.get(region);
        if (calendar == null) {
            throw new IllegalArgumentException("Unknown region " + region);
        }
        LocalDate d = referralDate;
        int counted = 0;
        while (counted < NOTICE_BUSINESS_DAYS) {
            d = d.plusDays(1);
            if (d.getDayOfWeek() == DayOfWeek.SATURDAY || d.getDayOfWeek() == DayOfWeek.SUNDAY) {
                continue;
            }
            if (calendar.isHoliday(d)) {
                continue;
            }
            counted++;
        }
        return d;
    }

    public interface HolidayCalendar {
        boolean isHoliday(LocalDate date);
    }

    public interface NoticeQueue {
        void schedule(String referralId, String claimId, LocalDate dueDate, LocalDate deferredUntil);
    }

    public record NoticeDueEvent(String referralId, String claimId, String region,
                                 LocalDate referralDate, LocalDate deferredUntil) {
    }
}
