/*
  Warnings:

  - Added the required column `caseType` to the `Client` table without a default value. This is not possible if the table is not empty.
  - Added the required column `verbalQuality` to the `Client` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Client" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "phone" TEXT,
    "incidentDate" DATETIME,
    "location" TEXT,
    "injuryDetails" TEXT,
    "medicalExpenses" DECIMAL,
    "insuranceCompany" TEXT,
    "lawyerNotes" TEXT,
    "caseType" TEXT NOT NULL,
    "verbalQuality" TEXT NOT NULL,
    "onboardedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
INSERT INTO "new_Client" ("email", "id", "incidentDate", "injuryDetails", "insuranceCompany", "lawyerNotes", "location", "medicalExpenses", "name", "onboardedAt", "phone", "updatedAt") SELECT "email", "id", "incidentDate", "injuryDetails", "insuranceCompany", "lawyerNotes", "location", "medicalExpenses", "name", "onboardedAt", "phone", "updatedAt" FROM "Client";
DROP TABLE "Client";
ALTER TABLE "new_Client" RENAME TO "Client";
CREATE UNIQUE INDEX "Client_email_key" ON "Client"("email");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
