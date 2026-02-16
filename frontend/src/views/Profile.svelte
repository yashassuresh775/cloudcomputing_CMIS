<script>
  import { me, updateMe } from '../lib/api.js';
  import { onMount } from 'svelte';

  export let accessToken;
  export let user;
  export let onLogout = () => {};
  export let onProfileUpdate = (updated) => {};

  let profile = user;
  let loading = true;
  let error = '';
  let editMode = false;
  let editClassYear = '';
  let editLinkedInUrl = '';
  let saveLoading = false;
  let saveError = '';

  onMount(async () => {
    if (!accessToken) {
      loading = false;
      if (user) {
        profile = user;
      } else {
        error = 'Not signed in';
      }
      return;
    }
    try {
      profile = await me(accessToken);
      editClassYear = profile.classYear || '';
      editLinkedInUrl = profile.linkedInUrl || '';
    } catch (e) {
      error = e.message;
      profile = null;
    } finally {
      loading = false;
    }
  });

  $: if (user && !profile && !loading) {
    profile = user;
    editClassYear = profile?.classYear || '';
    editLinkedInUrl = profile?.linkedInUrl || '';
  }

  async function saveProfile() {
    saveError = '';
    if (!editClassYear.trim() && !editLinkedInUrl.trim()) {
      saveError = 'Enter class year and/or LinkedIn URL';
      return;
    }
    saveLoading = true;
    try {
      const updated = await updateMe(accessToken, {
        classYear: editClassYear.trim() || undefined,
        linkedInUrl: editLinkedInUrl.trim() || undefined,
      });
      profile = updated;
      onProfileUpdate(updated);
      editMode = false;
    } catch (e) {
      saveError = e.message || 'Update failed';
    } finally {
      saveLoading = false;
    }
  }
</script>

<div class="card">
  <h2>Profile</h2>
  {#if loading}
    <p>Loading…</p>
  {:else if error}
    <div class="alert alert-error">{error}</div>
    <button class="btn btn-secondary" on:click={onLogout}>Log out</button>
  {:else if profile}
    <p class="welcome-back">Welcome back{profile.email ? `, ${profile.email.split('@')[0]}` : ''}!</p>
    <p><strong>Email:</strong> {profile.email}</p>
    <p><strong>Role:</strong> {profile.role}</p>
    {#if profile.classYear}
      <p><strong>Class year:</strong> {profile.classYear}</p>
    {/if}
    {#if profile.linkedUin}
      <p><strong>Linked UIN:</strong> {profile.linkedUin} (Former Student)</p>
    {:else}
      <p class="hint">To link your external account to an old Student UIN and transfer your history as FORMER_STUDENT, use <strong>Graduation Handover</strong>.</p>
    {/if}
    {#if profile.linkedInUrl}
      <p><strong>LinkedIn:</strong> <a href={profile.linkedInUrl} target="_blank" rel="noopener noreferrer">{profile.linkedInUrl}</a></p>
    {/if}

    {#if editMode}
      <div class="edit-form">
        <h3>Edit profile</h3>
        {#if saveError}
          <div class="alert alert-error">{saveError}</div>
        {/if}
        <div class="form-group">
          <label for="profile-class-year">Class year</label>
          <input id="profile-class-year" type="text" bind:value={editClassYear} placeholder="e.g. 26" />
        </div>
        <div class="form-group">
          <label for="profile-linkedin">LinkedIn URL</label>
          <input id="profile-linkedin" type="url" bind:value={editLinkedInUrl} placeholder="https://linkedin.com/in/..." />
        </div>
        <button class="btn btn-primary" on:click={saveProfile} disabled={saveLoading}>{saveLoading ? 'Saving…' : 'Save'}</button>
        <button class="btn btn-secondary" on:click={() => { editMode = false; saveError = ''; }}>Cancel</button>
      </div>
    {:else}
      <button class="btn btn-secondary" style="margin-top: 0.5rem;" on:click={() => { editMode = true; editClassYear = profile.classYear || ''; editLinkedInUrl = profile.linkedInUrl || ''; saveError = ''; }}>Edit profile</button>
    {/if}

    <button class="btn btn-secondary" style="margin-top: 1rem;" on:click={onLogout}>Log out</button>
  {/if}
</div>

<style>
  .welcome-back {
    font-size: 1.1rem;
    color: var(--primary-color);
    margin-bottom: 1rem;
  }
  .edit-form {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color, #ddd);
  }
  .edit-form .form-group {
    margin-bottom: 0.75rem;
  }
  .edit-form label {
    display: block;
    margin-bottom: 0.25rem;
  }
  .edit-form input {
    width: 100%;
    max-width: 320px;
    padding: 0.5rem;
  }
</style>
