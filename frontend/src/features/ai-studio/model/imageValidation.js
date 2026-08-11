export const MAX_AI_IMAGE_COUNT = 3;
export const MAX_AI_IMAGE_PAYLOAD_CHARACTERS = 28_000_000;

export function imagePayloadCharacters(images) {
  return (images || []).reduce((total, image) => {
    const dataUrl = typeof image === "string" ? image : image?.dataUrl;
    return total + String(dataUrl || "").length;
  }, 0);
}

export function estimatedImageDataUrlCharacters(file) {
  const prefix = `data:${file.type || "application/octet-stream"};base64,`;
  return prefix.length + 4 * Math.ceil((file.size || 0) / 3);
}

export function validateImagePayload(imageCount, payloadCharacters) {
  if (imageCount > MAX_AI_IMAGE_COUNT) {
    return `En fazla ${MAX_AI_IMAGE_COUNT} görsel eklenebilir.`;
  }
  if (payloadCharacters > MAX_AI_IMAGE_PAYLOAD_CHARACTERS) {
    return "Seçilen görseller 20 MB toplam istek sınırını aşıyor.";
  }
  return "";
}

export function selectValidImageFiles(existingImages, fileList) {
  const slots = Math.max(0, MAX_AI_IMAGE_COUNT - (existingImages || []).length);
  const candidates = Array.from(fileList || []).slice(0, slots);
  const acceptedFiles = [];
  const errors = [];
  let payloadCharacters = imagePayloadCharacters(existingImages);

  for (const file of candidates) {
    if (!file.type?.startsWith("image/")) {
      errors.push(`${file.name} bir görsel dosyası değil.`);
      continue;
    }
    const nextCharacters = payloadCharacters + estimatedImageDataUrlCharacters(file);
    const validationError = validateImagePayload(
      (existingImages || []).length + acceptedFiles.length + 1,
      nextCharacters
    );
    if (validationError) {
      errors.push(`${file.name}: ${validationError}`);
      continue;
    }
    payloadCharacters = nextCharacters;
    acceptedFiles.push(file);
  }

  return { acceptedFiles, errors };
}

export function validateImageDataUrl(existingImages, dataUrl) {
  return validateImagePayload(
    (existingImages || []).length + 1,
    imagePayloadCharacters(existingImages) + String(dataUrl || "").length
  );
}
