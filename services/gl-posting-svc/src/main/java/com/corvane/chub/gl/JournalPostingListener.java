package com.corvane.chub.gl;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Turns reserve, payment and recovery events into Group Ledger journal lines
 * (gl.journal_line). Lines are batched and posted to Group Ledger by the hourly
 * CLX-IF-050 job.
 */
@Component
public class JournalPostingListener {

    private final JournalLineRepository lines;
    private final AccountMapping accounts;

    public JournalPostingListener(JournalLineRepository lines, AccountMapping accounts) {
        this.lines = lines;
        this.accounts = accounts;
    }

    @KafkaListener(topics = "#{kafkaTopics.consumes()}", groupId = "gl-posting-svc")
    public void onEvent(FinanceEvent event) {
        lines.save(JournalLine.from(event, accounts.accountFor(event.type()), event.periodOf()));
    }
}
