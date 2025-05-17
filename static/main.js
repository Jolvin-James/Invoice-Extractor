document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('invoice_image');
  const previewContainer = document.getElementById('preview-container');
  const previewImage = document.getElementById('preview-image');

  // If the server already gave us an img src, show it:
  if (previewImage.src && !previewImage.src.endsWith('#')) {
    previewContainer.classList.remove('hidden');
  }

  // Only updates the preview when the user selects a new file:
  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      previewImage.src = e.target.result;
      previewContainer.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  });
});
