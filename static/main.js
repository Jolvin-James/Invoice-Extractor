// static/main.js
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('invoice_image');
  const previewContainer = document.getElementById('preview-container');
  const previewImage = document.getElementById('preview-image');

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) {
      previewContainer.classList.add('hidden');
      return;
    }
    const reader = new FileReader();
    reader.onload = e => {
      previewImage.src = e.target.result;
      previewContainer.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  });

  // The server‑side “show if img_data” logic is now handled in HTML below
});
