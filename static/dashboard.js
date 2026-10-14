(() => {
    const refreshIcons = () => window.lucide?.createIcons();
    const themeToggle = document.querySelector("#theme-toggle");
    const syncThemeToggle = () => {
        const isDark = document.documentElement.dataset.theme === "dark";
        const label = isDark ? "Aktifkan mode terang" : "Aktifkan mode gelap";
        themeToggle.setAttribute("aria-label", label);
        themeToggle.setAttribute("title", label);
        themeToggle.setAttribute("aria-pressed", String(isDark));
        themeToggle.innerHTML = `<i data-lucide="${isDark ? "sun" : "moon"}"></i>`;
        refreshIcons();
    };
    themeToggle.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = nextTheme;
        try { localStorage.setItem("sentube-theme", nextTheme); } catch { /* Storage may be disabled. */ }
        syncThemeToggle();
    });
    syncThemeToggle();
    const tabs = [...document.querySelectorAll("[data-tab]")];
    const forms = [...document.querySelectorAll("[data-analysis-form]")];
    const resultContainer = document.querySelector("#result-container");
    const csvForm = document.querySelector('[data-panel="csv"]');
    const csvInput = document.querySelector("#csv-file");
    const csvLabel = document.querySelector("[data-file-label]");
    const csvSummary = document.querySelector("[data-csv-summary]");
    const csvColumnInput = document.querySelector("#csv-text-column");
    const openEditorButton = document.querySelector("#open-csv-editor");
    const dialog = document.querySelector("#csv-editor");
    const table = document.querySelector("#csv-editor-table");
    const columnSelect = document.querySelector("#csv-column-select");
    const editorError = document.querySelector("#csv-editor-error");
    const pageSize = 25;
    let committed = null;
    let draft = null;
    let currentPage = 0;

    tabs.forEach((tab) => tab.addEventListener("click", () => {
        tabs.forEach((item) => {
            const active = item === tab;
            item.classList.toggle("active", active);
            item.setAttribute("aria-selected", String(active));
        });
        forms.forEach((form) => form.classList.toggle("hidden", form.dataset.panel !== tab.dataset.tab));
    }));

    const navLinks = [...document.querySelectorAll(".nav-link")];
    navLinks.forEach((link) => link.addEventListener("click", () => {
        navLinks.forEach((item) => item.classList.toggle("active", item === link));
    }));

    forms.forEach((form) => form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (form === csvForm && !committed) {
            setCsvMessage("Pilih file CSV dan terapkan perubahan di editor terlebih dahulu.", true);
            return;
        }
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        resultContainer.className = "loading-state";
        resultContainer.innerHTML = "<div><div class='spinner'></div><strong>Memproses analisis</strong><p>Menjalankan kedua model SVM.</p></div>";
        try {
            const body = new FormData(form);
            if (form === csvForm) {
                body.set("file", committed.file, committed.file.name);
                body.set("text_column", committed.textColumn);
            }
            const response = await fetch(form.action, { method: "POST", body });
            if (!response.ok) throw new Error(`Server merespons ${response.status}`);
            resultContainer.className = "";
            resultContainer.innerHTML = await response.text();
            refreshIcons();
        } catch (error) {
            resultContainer.className = "";
            const message = document.createElement("p");
            message.textContent = error.message;
            const wrapper = document.createElement("div");
            wrapper.className = "result-error";
            wrapper.innerHTML = "<i data-lucide='circle-alert'></i><div><strong>Permintaan gagal</strong></div>";
            wrapper.querySelector("div").append(message);
            resultContainer.replaceChildren(wrapper);
            refreshIcons();
        } finally {
            button.disabled = false;
        }
    }));

    function setCsvMessage(message, isError = false) {
        csvSummary.textContent = message;
        csvSummary.classList.toggle("error", isError);
    }

    function showEditorError(message) {
        editorError.textContent = message;
        editorError.hidden = !message;
    }

    function guessTextColumn(headers) {
        const known = ["text", "komentar", "comment", "tweet", "review", "content"];
        const found = headers.find((header) => known.includes(header.toLowerCase()));
        return found || headers[0];
    }

    function cloneData(data) {
        return {
            headers: [...data.headers],
            rows: data.rows.map((row) => [...row]),
            textColumn: data.textColumn,
            filename: data.filename,
        };
    }

    function openEditor(data) {
        draft = cloneData(data);
        currentPage = 0;
        showEditorError("");
        renderEditor();
        dialog.showModal();
        refreshIcons();
    }

    function renderEditor() {
        if (!draft) return;
        const totalPages = Math.max(1, Math.ceil(draft.rows.length / pageSize));
        currentPage = Math.min(currentPage, totalPages - 1);
        document.querySelector("#csv-modal-filename").textContent = draft.filename;
        document.querySelector("#csv-row-count").textContent = `${draft.rows.length.toLocaleString("id-ID")} baris`;
        document.querySelector("#csv-column-count").textContent = `${draft.headers.length} kolom`;
        document.querySelector("#csv-page-label").textContent = `Halaman ${currentPage + 1} dari ${totalPages}`;
        document.querySelector("#csv-prev-page").disabled = currentPage === 0;
        document.querySelector("#csv-next-page").disabled = currentPage >= totalPages - 1;

        columnSelect.replaceChildren();
        draft.headers.forEach((header) => {
            const option = new Option(header, header);
            columnSelect.add(option);
        });
        columnSelect.value = draft.textColumn;

        const headerRow = document.createElement("tr");
        for (const title of ["#", ...draft.headers, ""]) {
            const cell = document.createElement("th");
            cell.textContent = title;
            headerRow.append(cell);
        }
        table.tHead.replaceChildren(headerRow);

        const fragment = document.createDocumentFragment();
        const start = currentPage * pageSize;
        draft.rows.slice(start, start + pageSize).forEach((row, localIndex) => {
            const rowIndex = start + localIndex;
            const tr = document.createElement("tr");
            const number = document.createElement("td");
            number.className = "row-number";
            number.textContent = String(rowIndex + 1);
            tr.append(number);
            row.forEach((value, colIndex) => {
                const cell = document.createElement("td");
                const input = document.createElement("input");
                input.type = "text";
                input.value = value;
                input.title = value;
                input.dataset.row = String(rowIndex);
                input.dataset.col = String(colIndex);
                input.setAttribute("aria-label", `Baris ${rowIndex + 1}, ${draft.headers[colIndex]}`);
                cell.append(input);
                tr.append(cell);
            });
            const actions = document.createElement("td");
            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-row";
            deleteButton.dataset.deleteRow = String(rowIndex);
            deleteButton.title = `Hapus baris ${rowIndex + 1}`;
            deleteButton.setAttribute("aria-label", deleteButton.title);
            deleteButton.innerHTML = '<i data-lucide="trash-2"></i>';
            actions.append(deleteButton);
            tr.append(actions);
            fragment.append(tr);
        });
        table.tBodies[0].replaceChildren(fragment);
        refreshIcons();
    }

    function parseFile(file) {
        if (!file.name.toLowerCase().endsWith(".csv")) {
            setCsvMessage("File harus berformat .csv.", true);
            csvInput.value = "";
            return;
        }
        if (!window.Papa) {
            setCsvMessage("Parser CSV belum tersedia. Muat ulang halaman.", true);
            return;
        }
        setCsvMessage("Membaca CSV...");
        Papa.parse(file, {
            skipEmptyLines: "greedy",
            complete(result) {
                const records = result.data;
                if (result.errors.length || records.length < 2) {
                    setCsvMessage("CSV tidak valid atau tidak memiliki baris data.", true);
                    csvInput.value = "";
                    return;
                }
                const headers = records[0].map((value) => String(value).replace(/^\uFEFF/, "").trim());
                if (headers.some((header) => !header) || new Set(headers).size !== headers.length) {
                    setCsvMessage("Nama kolom CSV harus terisi dan unik.", true);
                    csvInput.value = "";
                    return;
                }
                const rows = records.slice(1).map((row) => headers.map((_, index) => String(row[index] ?? "")));
                openEditor({ headers, rows, textColumn: guessTextColumn(headers), filename: file.name });
            },
            error() {
                setCsvMessage("File CSV tidak dapat dibaca.", true);
                csvInput.value = "";
            },
        });
    }

    csvInput.addEventListener("change", () => {
        const file = csvInput.files[0];
        if (file) parseFile(file);
    });
    openEditorButton.addEventListener("click", () => { if (committed) openEditor(committed); });
    document.querySelector("#close-csv-editor").addEventListener("click", () => dialog.close());
    document.querySelector("#cancel-csv-editor").addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => {
        draft = null;
        if (!committed) csvInput.value = "";
        else csvLabel.textContent = committed.file.name;
        csvInput.required = !committed;
        openEditorButton.disabled = !committed;
    });
    columnSelect.addEventListener("change", () => { draft.textColumn = columnSelect.value; });
    table.addEventListener("input", (event) => {
        const { row, col } = event.target.dataset;
        if (row !== undefined && col !== undefined) {
            draft.rows[Number(row)][Number(col)] = event.target.value;
            event.target.title = event.target.value;
        }
    });
    table.addEventListener("click", (event) => {
        const button = event.target.closest("[data-delete-row]");
        if (!button || !draft) return;
        draft.rows.splice(Number(button.dataset.deleteRow), 1);
        renderEditor();
    });
    document.querySelector("#add-csv-row").addEventListener("click", () => {
        if (!draft) return;
        draft.rows.push(draft.headers.map(() => ""));
        currentPage = Math.floor((draft.rows.length - 1) / pageSize);
        renderEditor();
        table.tBodies[0].lastElementChild?.querySelector("input")?.focus();
    });
    document.querySelector("#csv-prev-page").addEventListener("click", () => { currentPage--; renderEditor(); });
    document.querySelector("#csv-next-page").addEventListener("click", () => { currentPage++; renderEditor(); });

    function createCsvFile(data) {
        const csv = Papa.unparse({ fields: data.headers, data: data.rows }, { newline: "\r\n", escapeFormulae: true });
        return new File(["\uFEFF", csv], data.filename, { type: "text/csv;charset=utf-8" });
    }

    document.querySelector("#apply-csv-editor").addEventListener("click", () => {
        if (!draft.rows.length) {
            showEditorError("Tambahkan setidaknya satu baris data.");
            return;
        }
        const textIndex = draft.headers.indexOf(draft.textColumn);
        const textCount = draft.rows.filter((row) => row[textIndex]?.trim()).length;
        if (!textCount) {
            showEditorError("Kolom komentar yang dipilih belum berisi teks.");
            return;
        }
        committed = { ...cloneData(draft), file: createCsvFile(draft) };
        csvColumnInput.value = committed.textColumn;
        csvLabel.textContent = committed.file.name;
        csvInput.required = false;
        setCsvMessage(`${committed.rows.length.toLocaleString("id-ID")} baris · kolom ${committed.textColumn}`);
        openEditorButton.disabled = false;
        dialog.close();
    });
    document.querySelector("#download-csv").addEventListener("click", () => {
        if (!draft) return;
        const file = createCsvFile(draft);
        const url = URL.createObjectURL(file);
        const link = document.createElement("a");
        link.href = url;
        link.download = file.name;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    });

    refreshIcons();
})();
