<script>
  import { graduationHandover, me } from '../lib/api.js';

  export let accessToken;
  export let onDone = () => {};
  export let onCancel = () => {};

  let uin = '';
  let classYear = '';
  let error = '';
  let success = '';
  let loading = false;

  async function handleSubmit() {
    error = '';
    success = '';
    const u = String(uin).trim();
    if (!u) {
      error = 'UIN is required';
      return;
    }
    loading = true;
    try {
      await graduationHandover(accessToken, {
        uin: u,
        classYear: classYear.trim() || undefined,
      });
      const updated = await me(accessToken);
      success = 'Your account is now linked to your student history.';
      onDone(updated);
    } catch (e) {
      error = e.message || 'Handover failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <h2>Graduation Handover</h2>
  <p class="hint">Link a new external account to an old Student UIN, transferring your history and changing your primary role to <strong>FORMER_STUDENT</strong>. Use this to claim your student record after graduation.</p>
  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}
  {#if success}
    <div class="alert alert-success">{success}</div>
  {/if}
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="uin">Student UIN</label>
      <input id="uin" type="text" bind:value={uin} placeholder="e.g. 123456789" />
    </div>
    <div class="form-group">
      <label for="handover-class-year">Class year (optional)</label>
      <input id="handover-class-year" type="text" bind:value={classYear} placeholder="e.g. 26" />
    </div>
    <button class="btn btn-primary" type="submit" disabled={loading}>
      {loading ? 'Linking…' : 'Link my student history'}
    </button>
    <button class="btn btn-secondary" type="button" on:click={onCancel} style="margin-left: 0.5rem;">
      Cancel
    </button>
  </form>
</div>
