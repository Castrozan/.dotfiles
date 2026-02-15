import { connectToBrowser, findPontoFrame } from './playwright-resolver.js';

async function listAllDaysFromPontoTable(frame) {
  return await frame.evaluate(() => {
    const tableRows = document.querySelectorAll('tr');
    const dayEntries = [];

    for (const row of tableRows) {
      const cells = row.querySelectorAll('td');
      if (cells.length < 5) continue;

      const rawDateText = cells[0]?.textContent?.trim() || '';
      const dateLines = rawDateText.split('\n').map(l => l.trim()).filter(Boolean);
      const dateText = dateLines[0] || '';
      const dayOfWeek = dateLines[dateLines.length - 1] || '';
      const escala = cells[1]?.textContent?.trim();
      const horario = cells[2]?.textContent?.trim();
      const marcacoesCell = cells[3];
      const marcacoes = marcacoesCell?.textContent?.trim() || marcacoesCell?.querySelector('a')?.textContent?.trim() || '';
      const situacoes = cells[4]?.textContent?.trim();

      dayEntries.push({ dateText, dayOfWeek, escala, horario, marcacoes, situacoes });
    }

    return dayEntries;
  });
}

function isWeekdayWithMissingEntries(entry) {
  return entry.horario === '4707' && entry.marcacoes.includes('Inserir marcações');
}

(async () => {
  const { browser, page } = await connectToBrowser();
  const frame = await findPontoFrame(page);

  if (!frame) {
    console.error('ponto frame not found — is the Senior page open?');
    await browser.close();
    process.exit(1);
  }

  const allDays = await listAllDaysFromPontoTable(frame);
  const pendingDays = allDays.filter(isWeekdayWithMissingEntries);

  console.log('=== All days ===');
  for (const day of allDays) {
    const status = day.marcacoes.includes('Inserir') ? '❌' : '✅';
    const dateDisplay = `${day.dateText} ${day.dayOfWeek || ''}`.padEnd(20);
    console.log(`${status} ${dateDisplay} ${day.horario}  ${day.marcacoes}`);
  }

  if (pendingDays.length > 0) {
    console.log(`\n=== ${pendingDays.length} weekday(s) pending ===`);
    for (const day of pendingDays) {
      console.log(`  ${day.dateText} (${day.dayOfWeek})`);
    }
  } else {
    console.log('\n✅ All weekdays are filled');
  }

  await browser.close();
})();
