$(function(){
    const $form = $("#downloadForm");
    const $url = $("#urlInput");
    const $meta = $("#metaSection");
    const $thumb = $("#thumbImg");
    const $title = $("#videoTitle");
    const $quality = $("#qualitySelect");
    const $loader = $("#loader");
    const $note = $("#note");

    let lastProbeUrl = "";
    let probeTimer = null;
    const DEBOUNCE_MS = 700;

    function showLoader() { $loader.show(); }
    function hideLoader() { $loader.hide(); }

    // Basic YouTube URL check to avoid unnecessary probes
    function looksLikeYouTube(u) {
        if (!u) return false;
        try {
            const parsed = new URL(u);
            const host = parsed.hostname.toLowerCase();
            return host.includes("youtube.com") || host.includes("youtu.be");
        } catch (e) {
            // if not a full URL, still allow probing for common patterns
            return /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/.test(u);
        }
    }

    function scheduleProbe() {
        clearTimeout(probeTimer);
        probeTimer = setTimeout(probeUrl, DEBOUNCE_MS);
    }

    // Trigger probe on paste, input, or when user stops typing
    $url.on("paste", function(){
        // small delay to let pasted value populate
        setTimeout(scheduleProbe, 50);
    });

    $url.on("input", function(){
        // auto-probe only if it looks like a YouTube link
        const val = $url.val().trim();
        if (val && looksLikeYouTube(val)) {
            scheduleProbe();
        } else {
            // hide meta if input cleared or not a youtube link
            $meta.hide();
            $quality.empty();
            $note.text("");
        }
    });

    // also probe on blur and Enter as fallback
    $url.on("blur", probeUrl);
    $url.on("keydown", function(e){
        if (e.key === "Enter") {
            e.preventDefault();
            probeUrl();
        }
    });

    function probeUrl() {
        const val = $url.val().trim();
        if (!val || val === lastProbeUrl) return;
        if (!looksLikeYouTube(val)) {
            $note.text("Please paste a valid YouTube link.");
            return;
        }
        lastProbeUrl = val;
        $meta.hide();
        $quality.empty();
        $note.text("");
        showLoader();

        $.ajax({
            url: "/probe",
            type: "POST",
            data: { url: val },
            dataType: "json",
            success: function(resp) {
                hideLoader();
                if (resp && resp.success) {
                    // populate thumbnail and title
                    $thumb.attr("src", resp.thumbnail || "");
                    $title.text(resp.title || "Untitled");
                    // populate quality options
                    $quality.empty();
                    $quality.append($('<option>').val("best").text("--select quality--"));
                    if (Array.isArray(resp.qualities) && resp.qualities.length) {
                        resp.qualities.forEach(function(q){
                            $quality.append($('<option>').val(q.value).text(q.label));
                        });
                    }
                    $meta.show();
                    $note.text("");
                } else {
                    $note.text(resp && resp.error ? resp.error : "Could not fetch video info.");
                }
            },
            error: function() {
                hideLoader();
                $note.text("Failed to fetch video info. Check the link or try again.");
            }
        });
    }

    $form.on("submit", function(e){
        e.preventDefault();
        // ensure meta is shown and quality selected
        if (!$meta.is(":visible")) {
            // try probing first
            probeUrl();
            $note.text("Fetching video info first. Please click Download again.");
            return;
        }

        showLoader();

        $.ajax({
            url: "/download",
            type: "POST",
            data: $form.serialize(),
            xhrFields: { responseType: 'blob' },
            success: function(data, status, xhr){
                hideLoader();
                const blob = new Blob([data], {type: "video/mp4"});
                const link = document.createElement("a");
                const url = window.URL.createObjectURL(blob);
                link.href = url;

                const disposition = xhr.getResponseHeader("Content-Disposition");
                let filename = "video.mp4";
                if (disposition && disposition.indexOf("filename=") !== -1) {
                    filename = disposition.split("filename=")[1].replace(/"/g, "");
                }
                link.download = filename;

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            },
            error: function(){
                hideLoader();
                alert("Download failed!");
            }
        });
    });
});