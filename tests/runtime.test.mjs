import test from 'node:test';import assert from 'node:assert/strict';import {normalizeOutput} from '../public/java-runner.js';
test('output normalization preserves meaningful whitespace',()=>{assert.equal(normalizeOutput('x\r\n'),'x');assert.notEqual(normalizeOutput('x '),'x');assert.notEqual(normalizeOutput('x\n\n'),'x');});
