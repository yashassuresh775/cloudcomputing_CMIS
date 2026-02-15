<script>
  import { signup } from '../lib/api.js';

  export let onDone = () => {};

  let email = '';
  let password = '';
  let confirmPassword = '';
  let formerStudent = false;
  let classYear = '';
  let error = '';
  let loading = false;

  async function handleSubmit() {
    error = '';
    if (!email.trim()) {
      error = 'Email is required';
      return;
    }
    if (!password) {
      error = 'Password is required';
      return;
    }
    if (password.length < 10) {
      error = 'Password must be at least 10 characters';
      return;
    }
    if (password !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }
    if (formerStudent && !classYear.trim()) {
      error = 'Class Year is required when claiming Former Student';
      return;
    }
    loading = true;
    try {
          await signup({
            email: email.trim().toLowerCase(),
            password,
            formerStudent,
            classYear: classYear.trim() || undefined,
          });
      onDone();
    } catch (e) {
      error = e.message || 'Registration failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <h2>Create account</h2>
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="reg-email">Email</label>
      <input id="reg-email" type="email" bind:value={email} required placeholder="you@company.com" />
    </div>
    <div class="form-group">
      <label for="reg-password">Password</label>
      <input id="reg-password" type="password" bind:value={password} required minlength="10" />
      <div class="hint">At least 10 characters</div>
    </div>
    <div class="form-group">
      <label for="reg-confirm">Confirm password</label>
      <input id="reg-confirm" type="password" bind:value={confirmPassword} required />
    </div>
    <div class="checkbox-group">
      <input id="former" type="checkbox" bind:checked={formerStudent} />
      <label for="former">I am a former student</label>
    </div>
    {#if formerStudent}
      <div class="form-group">
        <label for="class-year">Class year</label>
        <input id="class-year" type="text" bind:value={classYear} placeholder="e.g. 26 or 2026" />
        <div class="hint">Required when claiming former student</div>
      </div>
    {/if}
    <button class="btn btn-primary" type="submit" disabled={loading}>
      {loading ? 'Creating…' : 'Register'}
    </button>
  </form>
  <p class="hint" style="margin-top: 1rem;">
    Partner role is assigned if your email domain is on the company list. Otherwise you are a Friend, or Former Student if you check the box.
  </p>
</div>
