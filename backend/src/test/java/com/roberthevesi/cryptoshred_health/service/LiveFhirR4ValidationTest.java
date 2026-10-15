package com.roberthevesi.cryptoshred_health.service;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.context.support.DefaultProfileValidationSupport;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.hl7.fhir.common.hapi.validation.validator.FhirInstanceValidator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

/** Diagnostic evaluation: invalid exports are findings, not harness failures. */
@EnabledIfSystemProperty(named = "mie.live.fhir", matches = ".+")
class LiveFhirR4ValidationTest {
    @Test
    void validateUnmodifiedLiveBundlesAgainstBaseR4() throws Exception {
        var context = FhirContext.forR4Cached();
        var module = new FhirInstanceValidator(new DefaultProfileValidationSupport(context));
        module.setNoTerminologyChecks(true);
        module.setErrorForUnknownProfiles(false);
        var validator = context.newValidator();
        validator.registerValidatorModule(module);
        Path directory = Path.of(System.getProperty("mie.live.fhir"));
        Path output = directory.resolve("fhir-validation");
        Files.createDirectories(output);
        var reports = new ArrayList<Map<String, Object>>();
        try (var files = Files.list(directory)) {
            for (Path file : files.filter(p -> p.getFileName().toString().contains("-fhir-"))
                    .filter(p -> p.toString().endsWith(".json")).sorted().toList()) {
                byte[] bytes = Files.readAllBytes(file);
                var result = validator.validateWithResult(Files.readString(file));
                var issues = new ArrayList<Map<String, String>>();
                for (var message : result.getMessages()) {
                    issues.add(Map.of("severity", message.getSeverity().name(),
                        "location", String.valueOf(message.getLocationString()),
                        "message", message.getMessage()));
                }
                var report = new LinkedHashMap<String, Object>();
                report.put("file", file.getFileName().toString());
                report.put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
                report.put("successful", result.isSuccessful());
                report.put("issues", issues);
                reports.add(report);
                Files.writeString(output.resolve(file.getFileName() + ".outcome.json"),
                    context.newJsonParser().setPrettyPrint(true).encodeResourceToString(result.toOperationOutcome()));
            }
        }
        assertEquals(3, reports.size(), "All three live FHIR exports must be evaluated");
        new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(output.resolve("summary.json").toFile(),
            Map.of("validator", "HAPI FHIR 8.8.2", "fhir_version", "4.0.1",
                "scope", "base R4 structure and invariants; terminology checks disabled; UK Core packages not loaded",
                "reports", reports));
    }
}
