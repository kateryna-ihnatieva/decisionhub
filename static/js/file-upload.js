/**
 * File Upload Handler for Decision Making System
 * Handles Excel/CSV file uploads with drag & drop, validation, and preview
 */

class FileUploadHandler {
    constructor(options = {}) {
        this.dropZone = options.dropZone || '.file-drop-zone';
        this.fileInput = options.fileInput || '#file-input';
        this.previewContainer = options.previewContainer || '#file-preview';
        this.uploadButton = options.uploadButton || '#upload-file-btn';
        this.progressBar = options.progressBar || '#upload-progress';
        this.errorContainer = options.errorContainer || '#upload-error';
        this.successContainer = options.successContainer || '#upload-success';
        this.methodType = options.methodType || 'hierarchy';
        this.expectedCriteria = options.expectedCriteria || 0;
        this.expectedAlternatives = options.expectedAlternatives || 0;

        this.allowedTypes = ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv'];
        this.maxFileSize = 16 * 1024 * 1024; // 16MB

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupFileInput();
    }

    setupEventListeners() {
        // Upload button click
        $(this.uploadButton).on('click', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });

        // Download example button
        $('.download-example-btn').on('click', (e) => {
            e.preventDefault();
            this.downloadExample();
        });

        // Preview button
        $('.preview-file-btn').on('click', (e) => {
            e.preventDefault();
            this.previewFile();
        });
    }

    setupDragAndDrop() {
        const dropZone = $(this.dropZone);

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.on(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.on(eventName, () => {
                dropZone.addClass('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.on(eventName, () => {
                dropZone.removeClass('drag-over');
            });
        });

        // Handle dropped files
        dropZone.on('drop', (e) => {
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    }

    setupFileInput() {
        $(this.fileInput).on('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });
    }

    handleFileSelect(file) {
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.showError(validation.message);
            return;
        }

        // Show file info
        this.showFileInfo(file);

        // Enable upload button
        $(this.uploadButton).prop('disabled', false);

        // Store file for later use
        this.selectedFile = file;
    }

    validateFile(file) {
        // Check file type
        if (!this.allowedTypes.includes(file.type) &&
            !file.name.match(/\.(xlsx|xls|csv)$/i)) {
            return {
                valid: false,
                message: 'Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV file.'
            };
        }

        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                message: 'File too large. Maximum size is 16MB.'
            };
        }

        return { valid: true };
    }

    showFileInfo(file) {
        const fileInfo = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-excel"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <div class="file-actions">
                    <button type="button" class="btn btn-sm btn-outline-secondary preview-file-btn">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-file-btn">
                        <i class="fas fa-times"></i> Remove
                    </button>
                </div>
            </div>
        `;

        $(this.previewContainer).html(fileInfo);

        // Add remove file functionality
        $('.remove-file-btn').on('click', () => {
            this.removeFile();
        });
    }

    showError(message) {
        const errorHtml = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
        $(this.errorContainer).html(errorHtml);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            $(this.errorContainer).empty();
        }, 5000);
    }

    showSuccess(message) {
        const successHtml = `
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle"></i>
                ${message}
            </div>
        `;
        $(this.successContainer).html(successHtml);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            $(this.successContainer).empty();
        }, 5000);
    }

    showProgress(percent) {
        $(this.progressBar).css('width', percent + '%').attr('aria-valuenow', percent);
        $(this.progressBar).parent().show();
    }

    hideProgress() {
        $(this.progressBar).parent().hide();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    removeFile() {
        $(this.fileInput).val('');
        $(this.previewContainer).empty();
        $(this.uploadButton).prop('disabled', true);
        this.selectedFile = null;
    }

    async previewFile() {
        if (!this.selectedFile) {
            this.showError('No file selected');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('method_type', this.methodType);
        formData.append('expected_criteria', this.expectedCriteria);
        formData.append('expected_alternatives', this.expectedAlternatives);

        try {
            this.showProgress(50);

            const response = await fetch('/parse_file_preview', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showPreview(result.preview);
            } else {
                this.showError(result.error || 'Preview failed');
            }
        } catch (error) {
            this.showError('Network error during preview');
        } finally {
            this.hideProgress();
        }
    }

    showPreview(previewData) {
        let previewHtml = '<div class="preview-content">';

        if (previewData.criteria_names && previewData.criteria_names.length > 0) {
            previewHtml += `
                <div class="preview-section">
                    <h6><i class="fas fa-list"></i> Criteria Names</h6>
                    <div class="preview-list">
                        ${previewData.criteria_names.map(name => `<span class="badge badge-primary">${name}</span>`).join(' ')}
                    </div>
                </div>
            `;
        }

        if (previewData.alternative_names && previewData.alternative_names.length > 0) {
            previewHtml += `
                <div class="preview-section">
                    <h6><i class="fas fa-list"></i> Alternative Names</h6>
                    <div class="preview-list">
                        ${previewData.alternative_names.map(name => `<span class="badge badge-success">${name}</span>`).join(' ')}
                    </div>
                </div>
            `;
        }

        if (previewData.condition_names && previewData.condition_names.length > 0) {
            previewHtml += `
                <div class="preview-section">
                    <h6><i class="fas fa-list"></i> Condition Names</h6>
                    <div class="preview-list">
                        ${previewData.condition_names.map(name => `<span class="badge badge-info">${name}</span>`).join(' ')}
                    </div>
                </div>
            `;
        }

        if (previewData.matrices && previewData.matrices.length > 0) {
            previewHtml += `
                <div class="preview-section">
                    <h6><i class="fas fa-table"></i> Matrices Preview</h6>
                    <div class="preview-matrices">
                        ${previewData.matrices.map((matrix, index) => `
                            <div class="matrix-preview">
                                <h6>Matrix ${index + 1}</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm table-bordered">
                                        <thead>
                                            <tr>
                                                <th></th>
                                                ${matrix.names.map(name => `<th>${name}</th>`).join('')}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${matrix.matrix.map((row, i) => `
                                                <tr>
                                                    <td><strong>${matrix.names[i]}</strong></td>
                                                    ${row.map(cell => `<td>${cell}</td>`).join('')}
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (previewData.matrix && previewData.matrix.length > 0) {
            previewHtml += `
                <div class="preview-section">
                    <h6><i class="fas fa-table"></i> Matrix Preview</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-bordered">
                            <tbody>
                                ${previewData.matrix.map((row, i) => `
                                    <tr>
                                        ${row.map(cell => `<td>${cell}</td>`).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }

        previewHtml += '</div>';

        // Show in modal or dedicated preview area
        $('#previewModal .modal-body').html(previewHtml);
        $('#previewModal').modal('show');
    }

    async handleFileUpload() {
        if (!this.selectedFile) {
            this.showError('No file selected');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('method_type', this.methodType);
        formData.append('expected_criteria', this.expectedCriteria);
        formData.append('expected_alternatives', this.expectedAlternatives);

        try {
            this.showProgress(0);
            $(this.uploadButton).prop('disabled', true);

            const response = await fetch('/upload_file', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('File uploaded and parsed successfully!');
                this.handleUploadSuccess(result.data);
            } else {
                this.showError(result.error || 'Upload failed');
            }
        } catch (error) {
            this.showError('Network error during upload');
        } finally {
            this.hideProgress();
            $(this.uploadButton).prop('disabled', false);
        }
    }

    handleUploadSuccess(data) {
        // Fill form fields with uploaded data
        if (data.criteria_names && data.criteria_names.length > 0) {
            data.criteria_names.forEach((name, index) => {
                $(`input[name="name_criteria"][data-index="${index}"]`).val(name);
            });
        }

        if (data.alternative_names && data.alternative_names.length > 0) {
            data.alternative_names.forEach((name, index) => {
                $(`input[name="name_alternatives"][data-index="${index}"]`).val(name);
            });
        }

        // Show success message and auto-submit form after delay
        setTimeout(() => {
            $('form').submit();
        }, 2000);
    }

    downloadExample() {
        window.open(`/download_example/${this.methodType}`, '_blank');
    }
}

// Initialize file upload when DOM is ready
$(document).ready(function () {
    // Initialize for hierarchy method
    if ($('.hierarchy-upload').length > 0) {
        const hierarchyUpload = new FileUploadHandler({
            dropZone: '.hierarchy-upload .file-drop-zone',
            fileInput: '.hierarchy-upload #file-input',
            previewContainer: '.hierarchy-upload #file-preview',
            uploadButton: '.hierarchy-upload #upload-file-btn',
            progressBar: '.hierarchy-upload #upload-progress',
            errorContainer: '.hierarchy-upload #upload-error',
            successContainer: '.hierarchy-upload #upload-success',
            methodType: 'hierarchy',
            expectedCriteria: parseInt($('input[name="num_criteria"]').val()) || 0,
            expectedAlternatives: parseInt($('input[name="num_alternatives"]').val()) || 0
        });
    }

    // Initialize for other methods
    $('.method-upload').each(function () {
        const methodType = $(this).data('method-type');
        const expectedCriteria = parseInt($(this).data('expected-criteria')) || 0;
        const expectedAlternatives = parseInt($(this).data('expected-alternatives')) || 0;

        new FileUploadHandler({
            dropZone: $(this).find('.file-drop-zone'),
            fileInput: $(this).find('#file-input'),
            previewContainer: $(this).find('#file-preview'),
            uploadButton: $(this).find('#upload-file-btn'),
            progressBar: $(this).find('#upload-progress'),
            errorContainer: $(this).find('#upload-error'),
            successContainer: $(this).find('#upload-success'),
            methodType: methodType,
            expectedCriteria: expectedCriteria,
            expectedAlternatives: expectedAlternatives
        });
    });
});
