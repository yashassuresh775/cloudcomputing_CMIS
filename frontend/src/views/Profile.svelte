<script>
  import { me } from '../lib/api.js';
  import { onMount } from 'svelte';

  export let accessToken;
  export let user;
  export let onLogout = () => {};

  let profile = user;
  let loading = true;
  let error = '';

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
    } catch (e) {
      error = e.message;
      profile = null;
    } finally {
      loading = false;
    }
  });

  $: if (user && !profile && !loading) profile = user;
</script>

<div class="card">
  <h2>Profile</h2>
  {#if loading}
    <p>Loading…</p>
  {:else if error}
    <div class="alert alert-error">{error}</div>
    <button class="btn btn-secondary" on:click={onLogout}>Log out</button>
  {:else if profile}
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
    <button class="btn btn-secondary" style="margin-top: 1rem;" on:click={onLogout}>Log out</button>
  {/if}
</div>
