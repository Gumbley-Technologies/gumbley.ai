/* Gumbley AI — brand loader.
 *
 * loader.js is Open WebUI's own extension point: src/app.html loads it with
 * `defer` from /static/loader.js, and upstream ships it empty. Using it means
 * the two things below need no patch to app.html at all, so an upstream
 * rewrite of that file cannot undo them.
 *
 * 1. THE TAB TITLE BEFORE HYDRATION. app.html hard-codes <title>Open WebUI
 *    </title>; the Svelte app replaces it with the backend's WEBUI_NAME once
 *    it mounts. On a cold load that leaves the wrong name in the tab for as
 *    long as the bundle takes to boot.
 *
 * 2. THE ADDRESS-BAR / TASK-SWITCHER COLOUR. The inline script in app.html
 *    sets <meta name="theme-color"> to #171717 or #ffffff, and re-sets it
 *    whenever the OS theme flips. Setting it once here would be undone by
 *    that listener, so this observes the html class instead and re-applies.
 *
 * Both are cosmetic-but-visible; neither touches application behaviour.
 */
(function () {
	var BRAND = 'Gumbley AI';
	var DARK = '#0b1e2e'; /* --gaiBg  dark  */
	var LIGHT = '#f4f9fd'; /* --gaiBg  light */

	if (document.title === 'Open WebUI') {
		document.title = BRAND;
	}

	var meta = document.querySelector('meta[name="theme-color"]');
	if (!meta) return;

	function paint() {
		var want = document.documentElement.classList.contains('dark') ? DARK : LIGHT;
		if (meta.getAttribute('content') !== want) {
			meta.setAttribute('content', want);
		}
	}

	paint();

	/* The class flips on theme change and on the system-theme listener; the
	 * attribute flips when app.html's own code writes it back. Watch both. */
	new MutationObserver(paint).observe(document.documentElement, {
		attributes: true,
		attributeFilter: ['class']
	});
	new MutationObserver(paint).observe(meta, {
		attributes: true,
		attributeFilter: ['content']
	});
})();
