// Run against an explicit study-preview build, never the published Pages site.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const browser = await chromium.launch({
  executablePath: process.env.CHROME_BIN || '/etc/profiles/per-user/adrian/bin/google-chrome-stable',
  args: ['--no-sandbox'],
});
const context = await browser.newContext({viewport: {width: 390, height: 844}, acceptDownloads: true});
const page = await context.newPage();
const errors = [];
page.on('pageerror', error => errors.push(String(error)));
await page.route('https://raw.githubusercontent.com/adichannnnnhere64/jakarta-ee-question-bank/main/catalog.json',
  route => route.fulfill({path: 'content/enterprise/catalog.json', contentType: 'application/json'}));
const navigation = page.getByRole('navigation', {name: 'Learner navigation'});
const markers = page.getByRole('navigation', {name: 'Topic markers'});
const sections = page.getByRole('navigation', {name: 'Topic sections'});
const lesson = page.getByRole('article', {name: 'Study lesson'});
const state = () => page.evaluate(async () => JSON.parse(await window.tutorialz.load('learner-state')));
const noOverflow = async () => assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
const allTopics = () => page.getByRole('button', {name: '‹ All topics', exact: true}).click();

try {
  await page.goto(process.env.APP_URL || 'http://127.0.0.1:8876/');
  await navigation.getByRole('button', {name: 'Study', exact: true}).click();
  await page.getByRole('heading', {name: 'Understand it. Then practise it.'}).waitFor();
  assert.equal(await navigation.getByRole('button').count(), 5);
  assert.equal(await markers.getByRole('button').count(), 24);
  await noOverflow();
  await page.screenshot({path: '/tmp/tutorialz-study-index.png', fullPage: true});

  // All-word matching searches the lesson bodies as well as topic titles.
  await page.getByLabel('Find a topic or concept').fill('hibernate optimistic');
  assert(await markers.getByRole('button', {name: 'Hibernate', exact: true}).count() > 0);
  await markers.getByRole('button', {name: 'Hibernate', exact: true}).click();
  assert((await lesson.innerText()).includes('dirty checking'));
  await page.getByRole('button', {name: '☆ Save topic', exact: true}).click();
  await page.getByRole('button', {name: 'Mark topic as read', exact: true}).click();
  await sections.getByRole('button', {name: 'Cheatsheet', exact: true}).click();
  await lesson.getByRole('heading', {name: 'Cheatsheet', exact: true}).waitFor();
  assert((await lesson.innerText()).includes('org.hibernate.orm.jdbc.bind'));
  await noOverflow();
  await page.screenshot({path: '/tmp/tutorialz-study-hibernate.png', fullPage: true});
  await page.waitForFunction(async () => {
    const progress = JSON.parse(await window.tutorialz.load('learner-state')).progress.study;
    return progress.read.includes('hibernate') && progress.bookmarks.includes('hibernate') && progress.last_section_id === 'cheatsheet';
  });
  const before = await state();

  // Reading progress survives reload; returning to a topic resumes its section.
  await page.reload();
  await navigation.getByRole('button', {name: 'Study', exact: true}).click();
  await page.getByRole('button', {name: 'Continue: Hibernate', exact: true}).click();
  assert((await lesson.innerText()).includes('org.hibernate.orm.jdbc.bind'));
  await allTopics();
  await page.getByRole('group', {name: 'Filter study topics'}).getByRole('button', {name: 'Saved', exact: true}).click();
  assert.equal(await markers.getByRole('button').count(), 1);
  await markers.getByRole('button', {name: 'Hibernate', exact: true}).click();
  await page.getByRole('button', {name: '★ Saved', exact: true}).click();
  await allTopics();
  await page.getByText('No topics match.', {exact: false}).waitFor();
  await page.getByRole('group', {name: 'Filter study topics'}).getByRole('button', {name: 'Unread', exact: true}).click();
  assert.equal(await markers.getByRole('button').count(), 23);
  await page.getByRole('group', {name: 'Filter study topics'}).getByRole('button', {name: 'All topics', exact: true}).click();

  // Every section is embedded: reading requires no network fetches.
  await context.setOffline(true);
  const titles = await markers.getByRole('button').allTextContents();
  let sectionCount = 0;
  for (const title of titles) {
    await markers.getByRole('button', {name: title, exact: true}).click();
    assert.equal(await sections.getByRole('button').count(), 8, `${title}: incomplete chapter`);
    for (const name of await sections.getByRole('button').allTextContents()) {
      sectionCount++;
      await sections.getByRole('button', {name, exact: true}).click();
      await lesson.getByRole('heading', {name, exact: true}).waitFor();
      if (name === 'Sources') {
        assert(await lesson.getByRole('link').count() > 0, `${title}: missing sources`);
      } else {
        assert((await lesson.innerText()).length > 90, `${title}: empty ${name}`);
      }
      await noOverflow();
    }
    await allTopics();
  }
  assert.equal(sectionCount, 192);
  await context.setOffline(false);
  assert.deepEqual((await state()).progress.attempts, before.progress.attempts);
  assert.deepEqual((await state()).progress.active, before.progress.active);

  await page.getByLabel('Find a topic or concept').fill('Factory Method');
  await page.getByLabel('Matching sections in Design patterns').getByRole('button', {name: /Example P2/}).click();
  await lesson.getByRole('heading', {name: 'Apply', exact: true}).waitFor();
  await lesson.getByRole('heading', {name: 'Example P2: Factory Method', exact: true}).waitFor();
  await page.locator('.study-outline summary').click();
  await page.getByRole('navigation', {name: 'Chapter contents'}).getByRole('button', {name: 'Example P4: Builder with defensive copying', exact: true}).click();
  await lesson.getByRole('heading', {name: 'Example P4: Builder with defensive copying', exact: true}).waitFor();
  await page.waitForFunction(() => {
    const heading = document.getElementById('study-8-1-3');
    return heading && heading.getBoundingClientRect().top >= -1 && heading.getBoundingClientRect().top < innerHeight / 2;
  });
  await noOverflow();
  await page.screenshot({path: '/tmp/tutorialz-study-builder-expanded.png', fullPage: true});
  await page.setViewportSize({width: 320, height: 740});
  await noOverflow();
  await page.setViewportSize({width: 390, height: 844});

  // Progress export includes reading state; imported out-of-range cursors clamp safely.
  await navigation.getByRole('button', {name: 'Settings', exact: true}).click();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', {name: 'Export progress', exact: true}).click();
  const download = await downloading;
  const backup = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
  assert(backup.study.read.includes('hibernate'));
  const changed = await state();
  changed.progress.study.last_topic = 'jms';
  changed.progress.study.last_section = 999;
  delete changed.progress.study.last_section_id;
  await page.evaluate(value => window.tutorialz.save({key: 'learner-state', value: JSON.stringify(value)}), changed);
  await page.reload();
  await navigation.getByRole('button', {name: 'Study', exact: true}).click();
  await page.getByRole('button', {name: 'Continue: JMS', exact: true}).click();
  await lesson.getByRole('heading', {name: 'Understand', exact: true}).waitFor();
  await page.getByRole('button', {name: 'Next section →', exact: true}).click();
  await lesson.getByRole('heading', {name: 'Apply', exact: true}).waitFor();
  // A v0.3.4 Cheatsheet cursor remains Cheatsheet after Advanced is inserted.
  const legacy = await state();
  legacy.progress.study.last_topic = 'patterns';
  legacy.progress.study.last_section = 2;
  delete legacy.progress.study.last_section_id;
  await page.evaluate(value => window.tutorialz.save({key: 'learner-state', value: JSON.stringify(value)}), legacy);
  await page.reload();
  await navigation.getByRole('button', {name: 'Study', exact: true}).click();
  await page.getByRole('button', {name: 'Continue: Design patterns', exact: true}).click();
  await lesson.getByRole('heading', {name: 'Cheatsheet', exact: true}).waitFor();
  assert((await lesson.innerText()).includes('Factory Method'));
  assert((await lesson.innerText()).includes('Builder'));
  assert.deepEqual(errors, []);
  console.log(`PASS: 24 mobile study topics, ${sectionCount} offline sections, subtopic search, contents navigation, bookmarks, legacy cursor migration and narrow layout`);
} finally {
  await browser.close();
}
