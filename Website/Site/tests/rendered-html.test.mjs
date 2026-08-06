import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the company site and simulation launchers", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Loop Nopal Solutions/);
  assert.match(html, /Simulaciones ejecutables/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /\/simulaciones\/index\.html/);
  assert.match(html, /\/simulaciones\/v1\.html/);
  assert.match(html, /\/simulaciones\/v2\.html/);
  assert.match(html, /\/simulaciones\/v3\.html/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/);
});

test("ships every standalone simulation and the social image", async () => {
  await Promise.all([
    access(new URL("public/og.png", root)),
    access(new URL("public/simulaciones/index.html", root)),
    access(new URL("public/simulaciones/v1.html", root)),
    access(new URL("public/simulaciones/v2.html", root)),
    access(new URL("public/simulaciones/v3.html", root)),
  ]);
});
