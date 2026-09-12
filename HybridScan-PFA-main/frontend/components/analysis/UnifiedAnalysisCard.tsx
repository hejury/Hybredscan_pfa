"use client";

import { useEffect, useRef, useState, type DragEvent } from "react";
import { FolderSearch, UploadCloud } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Checkbox } from "@/components/ui/Checkbox";
import { Input } from "@/components/ui/Input";
import { Table, TableHead, TableHeadCell, TableBody, TableRow, TableCell, TableEmptyState } from "@/components/ui/Table";
import { VerdictBadge } from "@/components/analysis/VerdictBadge";
import { DetectionSourceBadge } from "@/components/analysis/DetectionSourceBadge";
import { AnalysisResultCard } from "@/components/analysis/AnalysisResultCard";
import { submitFileForAnalysis, MAX_UPLOAD_SIZE_MB, SUPPORTED_EXTENSIONS } from "@/lib/api/analysis";
import { fetchFolderScanConfig, launchFolderScan, FOLDER_SCAN_SUPPORTED_EXTENSIONS } from "@/lib/api/folderScan";
import { friendlyErrorMessage } from "@/lib/api/errorMessage";
import { formatFileSize, formatConfidence, cn, FAMILY_LABELS } from "@/lib/utils";
import type { AnalysisResult, FolderScanConfig, FolderScanSummary } from "@/lib/types/backend";

type OperationState<T> =
  | { status: "idle" }
  | { status: "running" }
  | { status: "success"; data: T }
  | { status: "error"; message: string };

function isSupportedFile(name: string): boolean {
  const lower = name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function friendlyFolderName(path: string): string {
  const trimmed = path.replace(/[\\/]+$/, "");
  const segments = trimmed.split(/[\\/]/);
  return segments[segments.length - 1] || trimmed;
}

export function UnifiedAnalysisCard() {
  // --- Fichier ---
  const [file, setFile] = useState<File | null>(null);
  const [fileValidationError, setFileValidationError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileState, setFileState] = useState<OperationState<AnalysisResult>>({ status: "idle" });
  const inputRef = useRef<HTMLInputElement>(null);

  // --- Dossier ---
  const [config, setConfig] = useState<FolderScanConfig | null>(null);
  const [folderPath, setFolderPath] = useState("");
  const [recursive, setRecursive] = useState(true);
  const [folderState, setFolderState] = useState<OperationState<FolderScanSummary>>({ status: "idle" });

  // --- Partagé ---
  const [autoQuarantine, setAutoQuarantine] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchFolderScanConfig().then((c) => {
      setConfig(c);
      if (c.configured && c.allowedRoots.length > 0) setFolderPath(c.allowedRoots[0]);
    });
  }, []);

  function acceptFile(candidate: File) {
    setFileValidationError(null);
    setFileState({ status: "idle" });

    if (!isSupportedFile(candidate.name)) {
      setFileValidationError(
        `Format non pris en charge. Formats acceptés : ${SUPPORTED_EXTENSIONS.join(", ")}.`
      );
      return;
    }

    if (candidate.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      setFileValidationError(`Fichier trop volumineux (max ${MAX_UPLOAD_SIZE_MB} Mo).`);
      return;
    }

    setFile(candidate);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) acceptFile(dropped);
  }

  const hasFile = file !== null && !fileValidationError;
  const hasFolder = folderPath.trim().length > 0;

  async function handleLaunch() {
    if (submitting || (!hasFile && !hasFolder)) return;

    setSubmitting(true);

    if (hasFile) setFileState({ status: "running" });
    if (hasFolder) setFolderState({ status: "running" });

    const filePromise = hasFile
      ? submitFileForAnalysis(file as File, { autoQuarantine }).then(
          (result) => setFileState({ status: "success", data: result }),
          (e) => setFileState({ status: "error", message: friendlyErrorMessage(e) })
        )
      : Promise.resolve();

    const folderPromise = hasFolder
      ? launchFolderScan({
          folderPath: folderPath.trim(),
          recursive,
          autoQuarantine,
        }).then(
          (summary) => setFolderState({ status: "success", data: summary }),
          (e) => setFolderState({ status: "error", message: friendlyErrorMessage(e) })
        )
      : Promise.resolve();

    await Promise.allSettled([filePromise, folderPromise]);
    setSubmitting(false);
  }

  const allowedRootsLabel =
    config && config.allowedRoots.length > 0
      ? config.allowedRoots.map(friendlyFolderName).join(", ")
      : null;

  return (
    <>
      <Card>
        <CardHeader
          title="Analyse"
          subtitle="Sélectionnez un fichier, un dossier, ou les deux."
        />

        {/* --- Fichier --- */}
        <p className="mb-2 text-sm font-bold text-ink">
          Fichier à analyser
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
          className={cn(
            "flex cursor-pointer flex-col items-center gap-2 rounded-md border-2 border-dashed px-6 py-8 text-center transition-colors",
            dragOver
              ? "border-primary bg-primary-soft"
              : "border-border bg-canvas-subtle hover:border-primary/60"
          )}
        >
          <UploadCloud className="h-7 w-7 text-primary" aria-hidden="true" />

          <p className="text-sm font-bold text-ink">
            Glissez-déposez un fichier ici, ou cliquez pour parcourir
          </p>

          <p className="text-xs text-ink-muted">
            Formats : {SUPPORTED_EXTENSIONS.join(", ")} · Taille maximale :{" "}
            {MAX_UPLOAD_SIZE_MB} Mo
          </p>

          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept={SUPPORTED_EXTENSIONS.join(",")}
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) acceptFile(selected);
            }}
          />
        </div>

        {file ? (
          <p className="mt-3 text-sm text-ink-secondary">
            Sélectionné :{" "}
            <span className="font-bold text-ink">{file.name}</span>{" "}
            ({formatFileSize(file.size)})
          </p>
        ) : null}

        {fileValidationError ? (
          <p className="mt-3 text-sm font-bold text-malicious">
            {fileValidationError}
          </p>
        ) : null}

        {fileState.status === "running" ? (
          <p className="mt-3 text-sm font-bold text-primary">
            Analyse du fichier en cours…
          </p>
        ) : null}

        {/* --- Séparateur --- */}
        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs font-bold uppercase tracking-wide text-ink-muted">
            ET / OU
          </span>
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* --- Dossier --- */}
        <div className="mb-2 flex items-center gap-2">
          <FolderSearch className="h-4 w-4 text-ink-secondary" aria-hidden="true" />
          <p className="text-sm font-bold text-ink">
            Dossier à scanner (optionnel)
          </p>
        </div>

        <p className="mb-3 text-xs text-ink-muted">
          Formats du scan dossier :{" "}
          {(config?.supportedExtensions ?? [...FOLDER_SCAN_SUPPORTED_EXTENSIONS]).join(", ")}.
          Les fichiers non pris en charge sont ignorés.
        </p>

        <Input
          id="folder-path"
          placeholder={config?.allowedRoots[0] ?? "Chargement de la configuration…"}
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          hint={
            config
              ? config.configured
                ? `Le scan de dossier s'exécute côté serveur dans le répertoire autorisé. Dossier autorisé : ${allowedRootsLabel}`
                : "Aucune racine de scan n'est configurée côté serveur."
              : "Chargement de la configuration…"
          }
        />

        <div className="mt-4 flex flex-col gap-3">
          <Checkbox
            id="folder-recursive"
            label="Inclure les sous-dossiers"
            checked={recursive}
            onChange={(e) => setRecursive(e.target.checked)}
          />

          <Checkbox
            id="shared-auto-quarantine"
            label="Quarantaine automatique"
            description="Isoler automatiquement tout fichier malveillant détecté (fichier analysé et/ou dossier scanné)."
            checked={autoQuarantine}
            onChange={(e) => setAutoQuarantine(e.target.checked)}
          />
        </div>

        {folderState.status === "running" ? (
          <p className="mt-3 text-sm font-bold text-primary">
            Scan du dossier en cours…
          </p>
        ) : null}

        {/* --- Action unique --- */}
        <Button
          className="mt-6 w-full"
          disabled={!hasFile && !hasFolder}
          loading={submitting}
          onClick={handleLaunch}
        >
          Lancer l&apos;analyse
        </Button>
      </Card>

      {(fileState.status === "success" ||
        fileState.status === "error" ||
        folderState.status === "success" ||
        folderState.status === "error") ? (
        <div className="flex flex-col gap-4">
          {fileState.status === "success" ? (
            <div>
              <p className="mb-2 text-sm font-bold text-ink-secondary">
                Résultat du fichier
              </p>
              <AnalysisResultCard result={fileState.data} />
            </div>
          ) : null}

          {fileState.status === "error" ? (
            <Card>
              <p className="text-sm font-bold text-ink-secondary">
                Résultat du fichier
              </p>
              <p className="mt-2 text-sm font-bold text-malicious">
                {fileState.message}
              </p>
            </Card>
          ) : null}

          {folderState.status === "success" ? (
            <div>
              <p className="mb-2 text-sm font-bold text-ink-secondary">
                Résultat du scan
              </p>

              <Card>
                <p className="mb-3 text-sm text-ink-secondary">
                  {folderState.data.filesExamined} fichier(s) examiné(s) —{" "}
                  {folderState.data.malicious} malveillant(s),{" "}
                  {folderState.data.healthy} sain(s),{" "}
                  {folderState.data.indeterminate} indéterminé(s)
                  {folderState.data.technicalErrors > 0
                    ? `, ${folderState.data.technicalErrors} erreur(s) technique(s)`
                    : ""}
                  .
                </p>

                <Table>
                  <TableHead>
                    <TableHeadCell>Fichier</TableHeadCell>
                    <TableHeadCell>Type</TableHeadCell>
                    <TableHeadCell>Verdict</TableHeadCell>
                    <TableHeadCell>Source</TableHeadCell>
                    <TableHeadCell>Probabilité malware</TableHeadCell>
                  </TableHead>

                  <TableBody>
                    {folderState.data.results.length === 0 ? (
                      <TableEmptyState
                        colSpan={5}
                        message="Aucun fichier éligible trouvé."
                      />
                    ) : (
                      folderState.data.results.map((item) => (
                        <TableRow key={item.relativePath}>
                          <TableCell className="font-technical break-all font-bold">
                            {item.relativePath}
                          </TableCell>

                          <TableCell>
                            {FAMILY_LABELS[item.family]}
                          </TableCell>

                          <TableCell>
                            <VerdictBadge verdict={item.verdict} />
                          </TableCell>

                          <TableCell>
                            <DetectionSourceBadge
                              source={item.detectionSource}
                            />
                          </TableCell>

                          <TableCell>
                            {formatConfidence(item.confidence)}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </Card>
            </div>
          ) : null}

          {folderState.status === "error" ? (
            <Card>
              <p className="text-sm font-bold text-ink-secondary">
                Résultat du scan
              </p>

              <p className="mt-2 text-sm font-bold text-malicious">
                Le scan du dossier n&apos;a pas pu être terminé.{" "}
                {folderState.message}
              </p>
            </Card>
          ) : null}
        </div>
      ) : null}
    </>
  );
}