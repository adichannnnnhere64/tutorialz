import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const browser = await chromium.launch({
  executablePath: process.env.CHROME_BIN || '/etc/profiles/per-user/adrian/bin/google-chrome-stable',
  args: ['--no-sandbox'],
});
const base = process.env.APP_URL || 'http://127.0.0.1:8766/';
const context = await browser.newContext();
const page = await context.newPage();
const errors = [];
page.on('pageerror', error => errors.push(String(error)));
const catalog = JSON.parse(await fs.readFile('content/enterprise/catalog.json', 'utf8'));
await page.route('https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json', route =>
  route.fulfill({ json: { ...catalog, content_revision: 0 } }));
try {
  await page.goto(base);
  await page.getByRole('heading', { name: 'Small steps. Stronger skills.' }).waitFor();
  await page.waitForFunction(async () => !!await window.tutorialz.load('learner-state'));
  const state = JSON.parse(await page.evaluate(() => window.tutorialz.load('learner-state')));
  const questions = state.courses.flatMap(c => c.tests.flatMap(t => t.questions));
  const ai = structuredClone(questions.find(q => q.id === 'java-oop-alias-mutation'));
  const scraped = questions.find(q => q.origin === 'scraped');
  const samples = JSON.parse(await fs.readFile('content/samples.json', 'utf8')).flatMap(c => c.tests.flatMap(t => t.questions));
  const multi = { ...structuredClone(ai), id: 'review-multiple', prompt: 'Which declarations compile?',
    options: ['int age = 1;', 'int 1age = 1;', 'long age = 1L;', 'var age;'], correct: [0, 2], multiple: true };
  const blanks = { ...structuredClone(samples.find(q => q.type === 'blanks')), id: 'review-blanks',
    blanks: [{ label: 'Number', accepted: ['4'], case_sensitive: false },
      { label: 'Text', accepted: ['safe'], case_sensitive: true }] };
  const code = { ...structuredClone(samples.find(q => q.type === 'java')), id: 'review-code' };
  code.cases = code.cases.map(testCase => ({ harness: '', ...testCase }));
  const skipped = { ...structuredClone(ai), id: 'review-skipped' };
  const unanswered = { ...structuredClone(ai), id: 'review-unanswered' };
  const snapshot = [ai, multi, blanks, code, skipped, unanswered, scraped];
  const wrongIndex = (ai.correct[0] + 1) % ai.options.length;
  const codeAnswer = 'System.out.print("wrong");\n// <script>untrusted</script>';
  const attempts = [
    [ai, { kind: 'choice', value: [wrongIndex] }, false],
    [multi, { kind: 'choice', value: [0, 1] }, false],
    [blanks, { kind: 'blanks', value: ['3', '  <script>untrusted</script>  '] }, false],
    [code, { kind: 'code', value: codeAnswer }, false],
    [skipped, { kind: 'skipped' }, false],
    [scraped, { kind: 'choice', value: scraped.correct }, true],
  ].map(([q, answer, correct], index) => ({ id: `review-attempt-${index}`, question_id: q.id,
    revision: q.revision, answer, correct, timestamp: index + 1 }));
  state.progress.attempts = attempts;
  state.progress.active = { id: 'review-session', questions: snapshot,
    answers: Object.fromEntries(attempts.map(a => [a.question_id, a])), drafts: {}, fast_mode: false, position: 0 };
  // Model an old cached default bank and verify the new bundle replaces it
  // without rewriting saved attempts or the active quiz's question snapshot.
  state.catalog.content_revision = 0;
  state.courses[0].tests[0].questions[0].prompt = 'Retired duplicate from the old bank';
  await page.evaluate(value => window.tutorialz.save({ key: 'learner-state', value: JSON.stringify(value) }), state);
  await page.reload();
  await page.getByRole('heading', { name: 'Small steps. Stronger skills.' }).waitFor();
  await page.waitForFunction(async () => JSON.parse(await window.tutorialz.load('learner-state')).catalog.content_revision === 1);
  const upgraded = JSON.parse(await page.evaluate(() => window.tutorialz.load('learner-state')));
  assert.notEqual(upgraded.courses[0].tests[0].questions[0].prompt, 'Retired duplicate from the old bank');
  assert.deepEqual(upgraded.progress.attempts, attempts);
  assert.deepEqual(upgraded.progress.active.questions, snapshot);
  await page.getByRole('button', { name: 'Start practicing' }).click();
  await page.getByRole('button', { name: 'Resume session', exact: true }).click();
  await page.locator('.feedback .submitted-answer').waitFor();
  assert((await page.locator('.feedback .submitted-answer').innerText()).includes(ai.options[wrongIndex].replaceAll('`', '')));
  await page.getByRole('button', { name: 'End session', exact: true }).click();
  await page.getByRole('button', { name: 'End & review', exact: true }).click();
  await page.getByRole('heading', { name: 'Every attempt counts.' }).waitFor();
  const rows = page.locator('.results-row');
  assert.equal(await rows.count(), snapshot.length);
  for (let index = 0; index < snapshot.length; index++) await rows.nth(index).locator('summary').click();
  assert((await rows.nth(0).locator('.submitted-answer').innerText()).includes(ai.options[wrongIndex].replaceAll('`', '')));
  assert((await rows.nth(0).innerText()).includes(ai.options[ai.correct[0]].replaceAll('`', '')));
  assert.equal(await rows.nth(1).locator('.submitted-answer li').count(), 2);
  assert((await rows.nth(1).locator('.submitted-answer').innerText()).includes('int 1age = 1;'));
  assert.equal(await rows.nth(2).locator('dd').nth(1).textContent(), '  <script>untrusted</script>  ');
  assert.equal(await rows.nth(2).locator('.submitted-answer script').count(), 0);
  assert.equal(await rows.nth(3).locator('.submitted-answer pre').textContent(), codeAnswer);
  assert((await rows.nth(4).innerText()).includes('You skipped this question.'));
  assert((await rows.nth(5).innerText()).includes('No answer submitted.'));
  assert.equal(await rows.nth(0).locator('.question-source .badge').textContent(), 'AI');
  assert.equal(await rows.nth(6).locator('.question-source .badge').textContent(), 'Scraped');
  assert((await rows.nth(6).locator('.question-source').innerText()).includes('Tahir Naseer'));
  assert.equal(await rows.nth(6).getByRole('link', { name: 'Source', exact: true }).getAttribute('href'), scraped.source_url);
  await page.screenshot({ path: '/tmp/tutorialz-question-review.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({ path: '/tmp/tutorialz-question-review-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 1280, height: 900 });
  const custom = JSON.parse(await page.evaluate(() => window.tutorialz.load('learner-state')));
  custom.catalog_url = 'https://example.com/custom/catalog.json';
  custom.catalog.content_revision = 0;
  custom.courses[0].tests[0].questions[0].prompt = 'A custom question kept by its owner';
  await page.route(custom.catalog_url, route => route.abort());
  await page.evaluate(value => window.tutorialz.save({ key: 'learner-state', value: JSON.stringify(value) }), custom);
  await page.reload();
  await page.getByRole('heading', { name: 'Small steps. Stronger skills.' }).waitFor();
  const customReloaded = JSON.parse(await page.evaluate(() => window.tutorialz.load('learner-state')));
  assert.equal(customReloaded.courses[0].tests[0].questions[0].prompt, 'A custom question kept by its owner');
  assert.equal(customReloaded.catalog.content_revision, 0);
  assert.deepEqual(errors, []);
  console.log('PASS: saved wrong answers for choice/multiple/blanks/code, skipped/unanswered, provenance, snapshot-preserving upgrade, stale catalog protection, mobile review');
} catch (error) {
  await page.screenshot({ path: '/tmp/tutorialz-review-failure.png', fullPage: true }).catch(() => {});
  throw error;
} finally {
  await browser.close();
}
