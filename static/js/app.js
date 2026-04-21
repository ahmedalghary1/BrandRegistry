const DEFAULT_EMPTY_LABEL = "غير محسوب";
const SAFE_STORAGE_KEY = "__registry_storage_test__";

function formatDateISOToArabic(isoValue) {
  if (!isoValue) {
    return DEFAULT_EMPTY_LABEL;
  }

  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) {
    return DEFAULT_EMPTY_LABEL;
  }

  return new Intl.DateTimeFormat("ar-EG", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function addDays(isoValue, days) {
  if (!isoValue) {
    return "";
  }

  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  date.setDate(date.getDate() + days);
  return date.toISOString().split("T")[0];
}

function addYears(isoValue, years) {
  if (!isoValue) {
    return "";
  }

  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const originalMonth = date.getMonth();
  date.setFullYear(date.getFullYear() + years);
  if (date.getMonth() !== originalMonth) {
    date.setDate(0);
  }

  return date.toISOString().split("T")[0];
}

function getSafeStorage() {
  try {
    window.localStorage.setItem(SAFE_STORAGE_KEY, "1");
    window.localStorage.removeItem(SAFE_STORAGE_KEY);
    return window.localStorage;
  } catch (error) {
    return null;
  }
}

function parseDecimal(value) {
  if (typeof value !== "string" && typeof value !== "number") {
    return 0;
  }

  const normalized = String(value).trim().replace(/,/g, "");
  if (!normalized) {
    return 0;
  }

  const parsedValue = Number.parseFloat(normalized);
  return Number.isFinite(parsedValue) ? parsedValue : 0;
}

function sumFees(form) {
  const feeFields = form.querySelectorAll(
    "[data-fee-field], [name='filing_fee'], [name='examination_fee'], [name='publication_fee'], [name='registration_fee'], [name='renewal_fee'], [name='appeal_fee'], [name='additional_fee']"
  );

  let total = 0;
  feeFields.forEach((field) => {
    total += parseDecimal(field.value);
  });

  return total.toFixed(2);
}

function toggleSidebar() {
  document.body.classList.toggle("sidebar-open");
}

function initDismissMessages() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-dismiss-parent]");
    if (!button) {
      return;
    }

    const parent = button.closest(".message");
    if (parent) {
      parent.remove();
    }
  });
}

function safeParseDraft(rawValue) {
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue);
  } catch (error) {
    return null;
  }
}

function setBannerMessage(target, message) {
  if (target) {
    target.textContent = message;
  }
}

function getFormField(form, roleName, fallbackSelector) {
  return form.querySelector(`[data-role='${roleName}']`) || form.querySelector(fallbackSelector);
}

function getFieldGroup(field) {
  return field?.closest(".field-group") || null;
}

function parseInteger(value) {
  const parsedValue = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsedValue) ? parsedValue : null;
}

function getRenewalRules(source) {
  const protectionYears = parseInteger(source?.dataset?.protectionYears) ?? 10;
  const renewalYears = parseInteger(source?.dataset?.renewalYears) ?? protectionYears;
  const maxRenewals = parseInteger(source?.dataset?.maxRenewals);
  return { protectionYears, renewalYears, maxRenewals };
}

function normalizeRenewalCount(renewalCount, rules = {}) {
  const parsedRenewalCount = parseInteger(renewalCount);
  if (parsedRenewalCount === null || parsedRenewalCount < 0) {
    return 0;
  }

  if (Number.isFinite(rules.maxRenewals)) {
    return Math.min(parsedRenewalCount, rules.maxRenewals);
  }

  return parsedRenewalCount;
}

function getProtectionExpiryISO(filingDate, renewalCount, rules = {}) {
  const parsedRenewalCount = normalizeRenewalCount(renewalCount, rules);
  const protectionYears = Number.isFinite(rules.protectionYears) ? rules.protectionYears : 10;
  const renewalYears = Number.isFinite(rules.renewalYears) ? rules.renewalYears : protectionYears;
  const totalYears = protectionYears + (renewalYears * parsedRenewalCount);
  return addYears(filingDate, totalYears);
}

function getRenewalStatus(status, filingDate, renewalCount, rules = {}) {
  if (!filingDate) {
    return DEFAULT_EMPTY_LABEL;
  }

  if (status !== "registered") {
    return "يتاح التجديد بعد التسجيل";
  }

  const parsedRenewalCount = normalizeRenewalCount(renewalCount, rules);
  const expiry = getProtectionExpiryISO(filingDate, renewalCount, rules);
  if (!expiry) {
    return DEFAULT_EMPTY_LABEL;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const expiryDate = new Date(expiry);
  expiryDate.setHours(0, 0, 0, 0);

  if (Number.isFinite(rules.maxRenewals) && parsedRenewalCount >= rules.maxRenewals) {
    if (expiryDate < today) {
      return "انتهت الحماية ولا يتاح تجديد إضافي";
    }
    return "تم استخدام كل مرات التجديد المتاحة";
  }

  if (expiryDate < today) {
    return "انتهت الحماية ويحتاج إلى تجديد";
  }

  if (parsedRenewalCount > 0) {
    return "تم التجديد";
  }

  return "يمكن التجديد بعد انتهاء الحماية";
}

function getProtectionStatus(filingDate, renewalCount, rules = {}) {
  const expiry = getProtectionExpiryISO(filingDate, renewalCount, rules);
  if (!expiry) {
    return DEFAULT_EMPTY_LABEL;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const expiryDate = new Date(expiry);
  expiryDate.setHours(0, 0, 0, 0);

  const parsedRenewalCount = normalizeRenewalCount(renewalCount, rules);
  const diffDays = Math.round((expiryDate - today) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return "منتهي";
  }

  if (diffDays <= 30) {
    return "على وشك الانتهاء";
  }

  if (Number.isFinite(parsedRenewalCount) && parsedRenewalCount > 0) {
    return "تم التجديد";
  }

  return "ساري";
}

function getFieldLabel(form, field) {
  if (!field?.id) {
    return null;
  }

  return (
    form.querySelector(`label[for="${field.id}"]`) ||
    document.querySelector(`label[for="${field.id}"]`)
  );
}

function ensureRequiredIndicator(label) {
  if (!label) {
    return null;
  }

  let indicator = label.querySelector(".required-indicator");
  if (!indicator) {
    indicator = document.createElement("span");
    indicator.className = "required-indicator";
    indicator.textContent = "*";
    indicator.title = "هذا الحقل إلزامي";
    indicator.setAttribute("aria-label", "هذا الحقل إلزامي");
    label.appendChild(indicator);
  }

  return indicator;
}

function syncRequiredIndicators(form) {
  form.querySelectorAll("input, select, textarea").forEach((field) => {
    if (!field.name || field.type === "hidden" || field.type === "file" || field.name === "csrfmiddlewaretoken") {
      return;
    }

    const label = getFieldLabel(form, field);
    const indicator = ensureRequiredIndicator(label);
    if (!indicator) {
      return;
    }

    const isVisible = !field.disabled && !field.closest("[hidden]");
    const isRequired = Boolean(field.required && isVisible);
    indicator.hidden = !isRequired;

    if (isRequired) {
      field.setAttribute("aria-required", "true");
    } else {
      field.removeAttribute("aria-required");
    }
  });
}

function syncFieldValidationState(field, forceInvalid = false) {
  const group = getFieldGroup(field);
  if (!group || !field) {
    return;
  }

  const hasServerError = Boolean(group.querySelector(".field-error"));
  const isHidden = Boolean(field.disabled || field.closest("[hidden]"));
  const isInvalid = !isHidden && (forceInvalid || hasServerError || (field.willValidate && !field.checkValidity()));

  field.classList.toggle("is-invalid", isInvalid);
  group.classList.toggle("has-error", isInvalid || hasServerError);
}

function initRecordForm(form) {
  if (!form || form.dataset.jsInitialized === "true") {
    return;
  }

  form.dataset.jsInitialized = "true";

  const storage = getSafeStorage();
  const statusField = getFormField(form, "status-field", "[name='status']");
  const publicationField = getFormField(form, "publication-date", "[name='publication_date']");
  const filingField = getFormField(form, "filing-date", "[name='filing_date']");
  const publicationPreview = form.querySelector("[data-derived='publication-deadline']");
  const protectionPreview = form.querySelector("[data-derived='protection-expiry']");
  const renewalStatusPreview = form.querySelector("[data-derived='renewal-status']");
  const protectionStatusPreview = form.querySelector("[data-derived='protection-status']");
  const totalFeesPreview = form.querySelector("[data-derived='total-fees']");
  const renewalCountField = form.querySelector("[name='renewal_count']");
  const visibilityBlocks = form.querySelectorAll("[data-visible-for]");
  const imageInput = getFormField(form, "image-input", "[name='image']");
  const imagePreview = form.querySelector("[data-role='image-preview']");
  const draftKey = form.dataset.autosaveKey;
  const draftBanner = form.querySelector("[data-role='draft-banner']");
  const draftStatus = form.querySelector("[data-role='draft-status']");
  const restoreButton = form.querySelector("[data-role='restore-draft']");
  const discardButton = form.querySelector("[data-role='discard-draft']");
  const renewalRules = getRenewalRules(form);
  let draftTimer = null;

  function computeDerivedValues() {
    if (publicationPreview) {
      publicationPreview.value = formatDateISOToArabic(addDays(publicationField?.value, 60));
    }

    if (protectionPreview) {
      protectionPreview.value = formatDateISOToArabic(
        getProtectionExpiryISO(filingField?.value, renewalCountField?.value, renewalRules)
      );
    }

    if (renewalStatusPreview) {
      renewalStatusPreview.value = getRenewalStatus(
        statusField?.value,
        filingField?.value,
        renewalCountField?.value,
        renewalRules
      );
    }

    if (protectionStatusPreview) {
      protectionStatusPreview.value = getProtectionStatus(
        filingField?.value,
        renewalCountField?.value,
        renewalRules
      );
    }

    if (totalFeesPreview) {
      totalFeesPreview.value = sumFees(form);
    }
  }

  function toggleVisibility() {
    const currentStatus = statusField ? statusField.value : "";

    visibilityBlocks.forEach((block) => {
      const visibleFor = (block.dataset.visibleFor || "all")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      const shouldShow = visibleFor.includes("all") || visibleFor.includes(currentStatus);
      block.hidden = !shouldShow;
    });

    form.querySelectorAll("input, select, textarea").forEach((field) => {
      if (field === statusField || field.dataset.alwaysEnabled === "true") {
        return;
      }

      field.dataset.originalRequired ||= field.required ? "true" : "false";

      const hiddenAncestor = field.closest("[hidden]");
      if (hiddenAncestor) {
        field.required = false;
        field.disabled = true;
        return;
      }

      field.disabled = false;

      const requiredFor = (field.dataset.requiredFor || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

      if (requiredFor.includes(currentStatus)) {
        field.required = true;
      } else if (field.dataset.originalRequired === "true" && !field.dataset.requiredFor) {
        field.required = true;
      } else {
        field.required = false;
      }

      syncFieldValidationState(field, false);
    });

    syncRequiredIndicators(form);
  }

  function previewImage(file) {
    if (!imagePreview || !file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      imagePreview.innerHTML = `<img src="${event.target?.result || ""}" alt="معاينة الصورة">`;
    };
    reader.readAsDataURL(file);
  }

  function getFormSnapshot() {
    const snapshot = {};

    form.querySelectorAll("input, select, textarea").forEach((field) => {
      if (!field.name || field.type === "file" || field.name === "csrfmiddlewaretoken") {
        return;
      }

      if (field.type === "checkbox") {
        snapshot[field.name] = field.checked;
      } else {
        snapshot[field.name] = field.value;
      }
    });

    return snapshot;
  }

  function applySnapshot(snapshot) {
    Object.entries(snapshot || {}).forEach(([name, value]) => {
      const field = form.querySelector(`[name="${name}"]`);
      if (!field) {
        return;
      }

      if (field.type === "checkbox") {
        field.checked = Boolean(value);
      } else {
        field.value = value;
      }

      field.dispatchEvent(new Event("change", { bubbles: true }));
      field.dispatchEvent(new Event("input", { bubbles: true }));
    });
  }

  function saveDraft() {
    if (!storage || !draftKey) {
      return;
    }

    try {
      const payload = {
        savedAt: new Date().toISOString(),
        values: getFormSnapshot(),
      };
      storage.setItem(draftKey, JSON.stringify(payload));
      setBannerMessage(draftStatus, "تم حفظ المسودة محليًا على هذا الجهاز.");
    } catch (error) {
      setBannerMessage(draftStatus, "تعذر حفظ المسودة محليًا. يمكنك متابعة الإدخال والحفظ يدويًا.");
    }
  }

  function scheduleDraftSave() {
    if (!storage || !draftKey) {
      return;
    }

    window.clearTimeout(draftTimer);
    draftTimer = window.setTimeout(saveDraft, 180);
  }

  function clearDraft() {
    window.clearTimeout(draftTimer);

    if (storage && draftKey) {
      try {
        storage.removeItem(draftKey);
      } catch (error) {
        // Ignore storage cleanup errors to keep the form usable.
      }
    }

    if (draftBanner) {
      draftBanner.classList.remove("is-visible");
    }
  }

  if (statusField) {
    statusField.addEventListener("change", () => {
      toggleVisibility();
      computeDerivedValues();
      scheduleDraftSave();
    });
  }

  [publicationField, filingField, renewalCountField].forEach((field) => {
    if (!field) {
      return;
    }

    field.addEventListener("change", computeDerivedValues);
    field.addEventListener("input", computeDerivedValues);
  });

  form
    .querySelectorAll(
      "[data-fee-field], [name='filing_fee'], [name='examination_fee'], [name='publication_fee'], [name='registration_fee'], [name='renewal_fee'], [name='appeal_fee'], [name='additional_fee']"
    )
    .forEach((field) => {
      field.addEventListener("input", () => {
        computeDerivedValues();
        scheduleDraftSave();
      });
      field.addEventListener("change", () => {
        computeDerivedValues();
        scheduleDraftSave();
      });
    });

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    if (field.type === "file") {
      return;
    }

    syncFieldValidationState(field, false);

    field.addEventListener("input", scheduleDraftSave);
    field.addEventListener("change", scheduleDraftSave);
    field.addEventListener("input", () => syncFieldValidationState(field, false));
    field.addEventListener("change", () => syncFieldValidationState(field, false));
  });

  if (imageInput) {
    imageInput.addEventListener("change", () => {
      previewImage(imageInput.files?.[0]);
    });
  }

  if (draftKey && draftBanner && storage) {
    const payload = safeParseDraft(storage.getItem(draftKey));

    if (payload?.savedAt) {
      draftBanner.classList.add("is-visible");
      setBannerMessage(
        draftStatus,
        `توجد مسودة محفوظة محليًا بتاريخ ${new Intl.DateTimeFormat("ar-EG", {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(new Date(payload.savedAt))}.`
      );
    } else if (storage.getItem(draftKey)) {
      storage.removeItem(draftKey);
    }

    restoreButton?.addEventListener("click", () => {
      applySnapshot(payload?.values || {});
      computeDerivedValues();
      toggleVisibility();
      draftBanner.classList.remove("is-visible");
    });

    discardButton?.addEventListener("click", clearDraft);
  }

  form.addEventListener("submit", (event) => {
    let firstInvalidField = null;

    form.querySelectorAll("input, select, textarea").forEach((field) => {
      if (!field.name || field.disabled || field.closest("[hidden]")) {
        syncFieldValidationState(field, false);
        return;
      }

      const invalid = field.willValidate && !field.checkValidity();
      syncFieldValidationState(field, invalid);

      if (invalid && !firstInvalidField) {
        firstInvalidField = field;
      }
    });

    if (firstInvalidField) {
      event.preventDefault();
      firstInvalidField.focus({ preventScroll: false });
      firstInvalidField.reportValidity();
      return;
    }

    clearDraft();
  });

  toggleVisibility();
  computeDerivedValues();
  syncRequiredIndicators(form);
}

function initApp() {
  const toggleButton = document.querySelector("[data-role='sidebar-toggle']");
  toggleButton?.addEventListener("click", toggleSidebar);

  initDismissMessages();

  document.querySelectorAll("[data-record-form], [data-enhanced-form]").forEach((form) => {
    initRecordForm(form);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}
