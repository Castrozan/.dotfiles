import { connectToBrowser, findPontoFrame } from './cdp-browser.js';

async function dismissRetroativoConfirmationDialog(frame, page) {
  await page.waitForTimeout(1000);
  const retroativoDialog = await frame.$('.ngdialog');
  if (retroativoDialog) {
    const simButton = await frame.$('.ngdialog button:has-text("Sim")');
    if (simButton) {
      await simButton.click();
      console.log('  dismissed "Acerto retroativo" → Sim');
      await page.waitForTimeout(2000);
    }
  }
}

async function selectEsquecimentoDeBatidaJustificativa(frame, page) {
  const justificativaDropdown = await frame.$('.p-dropdown, [class*=dropdown]');
  if (!justificativaDropdown) return false;

  await justificativaDropdown.click();
  await page.waitForTimeout(1000);

  const esquecimentoOption = await frame.$(
    'li:has-text("Esquecimento de Batida"), .p-dropdown-item:has-text("Esquecimento")'
  );

  if (!esquecimentoOption) {
    console.log('  could not find "Esquecimento de Batida" option');
    return false;
  }

  await esquecimentoOption.click();
  console.log('  selected "Esquecimento de Batida"');
  await page.waitForTimeout(500);

  const confirmarButton = await frame.$('button:has-text("Confirmar")');
  if (confirmarButton) {
    await confirmarButton.click();
    console.log('  clicked "Confirmar"');
    await page.waitForTimeout(2000);
  }

  return true;
}

async function fillSingleDayWithPrevistaEntries(frame, page, dateText) {
  console.log(`\n=== ${dateText} ===`);

  const allRows = await frame.$$('tr');
  let matchingRow = null;

  for (const row of allRows) {
    const firstCell = await row.$('td:first-child');
    if (!firstCell) continue;
    const cellText = await firstCell.textContent();
    if (cellText?.includes(dateText)) { matchingRow = row; break; }
  }

  if (!matchingRow) { console.log('  row not found'); return false; }

  const inserirMarcacoesLink = await matchingRow.$('a:has-text("Inserir marcações")');
  if (!inserirMarcacoesLink) { console.log('  already filled or no link'); return false; }

  await inserirMarcacoesLink.click({ force: true });
  await page.waitForTimeout(2500);

  const inserirPrevistasButton = await frame.$('button:has-text("Inserir previstas")');
  if (!inserirPrevistasButton) { console.log('  "Inserir previstas" button not found'); return false; }

  await inserirPrevistasButton.click();
  console.log('  clicked "Inserir previstas"');
  await page.waitForTimeout(2500);

  const justificativaSelected = await selectEsquecimentoDeBatidaJustificativa(frame, page);
  if (!justificativaSelected) return false;

  const salvarButton = await frame.$('button:has-text("Salvar")');
  if (salvarButton) {
    await salvarButton.click();
    console.log('  clicked "Salvar"');
    await page.waitForTimeout(2000);
  }

  await dismissRetroativoConfirmationDialog(frame, page);

  console.log(`  ${dateText}: DONE ✓`);
  return true;
}

function identifyPendingWeekdays(allDays) {
  return allDays
    .filter(d => d.horario === '4707' && d.marcacoes.includes('Inserir marcações'))
    .map(d => d.dateText.split('\n')[0].trim());
}

async function listAllDaysFromTable(frame) {
  return await frame.evaluate(() => {
    const rows = document.querySelectorAll('tr');
    const entries = [];
    for (const row of rows) {
      const cells = row.querySelectorAll('td');
      if (cells.length < 5) continue;
      entries.push({
        dateText: cells[0]?.textContent?.trim(),
        horario: cells[2]?.textContent?.trim(),
        marcacoes: cells[3]?.textContent?.trim()
      });
    }
    return entries;
  });
}

(async () => {
  const { browser, page } = await connectToBrowser();
  const frame = await findPontoFrame(page);

  if (!frame) {
    console.error('ponto frame not found — is the Senior page open?');
    await browser.close();
    process.exit(1);
  }

  const targetDate = process.argv[2];

  if (!targetDate) {
    console.log('usage: node ponto-fill.js <date|all>');
    console.log('  date: DD/MM format (e.g. 09/02)');
    console.log('  all: fill all pending weekdays automatically');
    await browser.close();
    process.exit(1);
  }

  if (targetDate === 'all') {
    const allDays = await listAllDaysFromTable(frame);
    const pendingDates = identifyPendingWeekdays(allDays);

    if (pendingDates.length === 0) {
      console.log('✅ No pending weekdays to fill');
      await browser.close();
      return;
    }

    console.log(`Found ${pendingDates.length} pending weekday(s): ${pendingDates.join(', ')}`);
    let successCount = 0;

    for (const date of pendingDates) {
      try {
        const success = await fillSingleDayWithPrevistaEntries(frame, page, date);
        if (success) successCount++;
      } catch (error) {
        console.log(`  ${date}: ERROR - ${error.message?.substring(0, 100)}`);
        await dismissRetroativoConfirmationDialog(frame, page);
        try {
          const cancelButton = await frame.$('button:has-text("Cancelar")');
          if (cancelButton) await cancelButton.click();
        } catch {}
      }
      await page.waitForTimeout(1500);
    }

    console.log(`\n=== SUMMARY: ${successCount}/${pendingDates.length} days filled ===`);
  } else {
    await fillSingleDayWithPrevistaEntries(frame, page, targetDate);
  }

  await page.screenshot({ path: '/tmp/ponto-result.png' });
  await browser.close();
})();
