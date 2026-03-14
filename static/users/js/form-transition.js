document.addEventListener('DOMContentLoaded', function () {
    const stepOneForm = document.getElementById('step-one-form');
    const stepTwoForm = document.getElementById('step-two-form');
    const nextBtn = document.getElementById('nextBtn');
    const backBtn = document.getElementById('backBtn');

    if (!nextBtn) return;

    nextBtn.addEventListener('click', function () {
        // Validate step 1 fields before proceeding
        const username = stepOneForm.querySelector('input[name="username"]');
        const firstName = stepOneForm.querySelector('input[name="first_name"]');
        const lastName = stepOneForm.querySelector('input[name="last_name"]');

        if (!username.value.trim() || !firstName.value.trim() || !lastName.value.trim()) {
            username.reportValidity();
            return;
        }

        stepOneForm.style.display = 'none';
        stepTwoForm.style.display = 'block';
    });

    if (backBtn) {
        backBtn.addEventListener('click', function () {
            stepTwoForm.style.display = 'none';
            stepOneForm.style.display = 'block';
        });
    }
});
