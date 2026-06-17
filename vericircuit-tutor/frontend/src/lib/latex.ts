import type { KatexOptions } from "katex";

const CODE_PLACEHOLDER_PREFIX = "CITT_PROTECTED_CODE";

export const katexOptions = {
  throwOnError: false,
  strict: false,
  trust: false,
  macros: {
    "\\SI": "{#1}\\,\\mathrm{#2}",
    "\\si": "\\mathrm{#1}",
    "\\ohm": "\\Omega",
    "\\degree": "^{\\circ}",
    "\\celsius": "^{\\circ}\\mathrm{C}",
    "\\micro": "\\mu",
    "\\nano": "\\mathrm{n}",
    "\\pico": "\\mathrm{p}",
    "\\milli": "\\mathrm{m}",
    "\\kilo": "\\mathrm{k}",
    "\\mega": "\\mathrm{M}",
    "\\giga": "\\mathrm{G}",
    "\\volt": "\\mathrm{V}",
    "\\ampere": "\\mathrm{A}",
    "\\watt": "\\mathrm{W}",
    "\\farad": "\\mathrm{F}",
    "\\henry": "\\mathrm{H}",
    "\\second": "\\mathrm{s}",
    "\\hertz": "\\mathrm{Hz}",
    "\\rms": "\\mathrm{rms}",
    "\\pk": "\\mathrm{pk}",
    "\\phasor": "\\underline{#1}",
    "\\node": "\\mathrm{#1}",
    "\\mat": "\\mathbf{#1}",
    "\\vect": "\\mathbf{#1}"
  }
} satisfies KatexOptions;

export function normalizeTutorLatex(markdown: string): string {
  const protectedBlocks: string[] = [];
  let normalized = markdown.replace(/\r\n?/g, "\n");

  normalized = protectCode(normalized, protectedBlocks);
  normalized = normalizeDisplayEnvironments(normalized);
  normalized = normalized
    .replace(/\\\[((?:.|\n)*?)\\\]/g, (_, equation: string) => `\n$$\n${equation.trim()}\n$$\n`)
    .replace(/\\\(((?:.|\n)*?)\\\)/g, (_, equation: string) => `$${equation.trim()}$`);

  return restoreCode(normalized, protectedBlocks);
}

function normalizeDisplayEnvironments(markdown: string): string {
  return markdown
    .replace(
      /\\begin\{equation\*?\}([\s\S]*?)\\end\{equation\*?\}/g,
      (_, equation: string) => `\n$$\n${equation.trim()}\n$$\n`
    )
    .replace(
      /\\begin\{align\*?\}([\s\S]*?)\\end\{align\*?\}/g,
      (_, equation: string) => `\n$$\n\\begin{aligned}\n${equation.trim()}\n\\end{aligned}\n$$\n`
    )
    .replace(
      /\\begin\{gather\*?\}([\s\S]*?)\\end\{gather\*?\}/g,
      (_, equation: string) => `\n$$\n\\begin{gathered}\n${equation.trim()}\n\\end{gathered}\n$$\n`
    );
}

function protectCode(markdown: string, protectedBlocks: string[]): string {
  const protect = (match: string) => {
    const index = protectedBlocks.push(match) - 1;
    return `${CODE_PLACEHOLDER_PREFIX}_${index}`;
  };

  return markdown
    .replace(/(```[\s\S]*?```|~~~[\s\S]*?~~~)/g, protect)
    .replace(/`[^`\n]*`/g, protect);
}

function restoreCode(markdown: string, protectedBlocks: string[]): string {
  return markdown.replace(
    new RegExp(`${CODE_PLACEHOLDER_PREFIX}_(\\d+)`, "g"),
    (_, index: string) => protectedBlocks[Number(index)] ?? ""
  );
}
