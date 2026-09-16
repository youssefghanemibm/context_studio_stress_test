package com.corvane.chub.payment;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Builds payment instructions for the Corvane Payments Gateway (CLX-IF-038, ISO 20022
 * pain.001 mapping) once a settlement is agreed and the payment is authorised (BR-STL-002)
 * and screened.
 */
@Service
public class PaymentInstructionService {

    static final String IDEMPOTENCY_HEADER = "Idempotency-Key";

    private final PaymentInstructionRepository instructions;
    private final CpgClient cpg;

    public PaymentInstructionService(PaymentInstructionRepository instructions, CpgClient cpg) {
        this.instructions = instructions;
        this.cpg = cpg;
    }

    @Transactional
    public PaymentInstruction submit(PaymentInstruction instruction) {
        instruction.setIdempotencyKey(idempotencyKey(instruction));
        instructions.save(instruction);
        // ADR-021: a retry after a CPG timeout re-sends the same key, so CPG drops the duplicate
        cpg.send(instruction, IDEMPOTENCY_HEADER, instruction.getIdempotencyKey());
        instruction.markSubmitted();
        return instruction;
    }

    static String idempotencyKey(PaymentInstruction instruction) {
        return "PAY-" + instruction.getPaymentId();
    }
}
