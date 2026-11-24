# UNIVERSAL FACE PIPELINE VIA TIDMUNZ STUDIO
Applies to EVERY story. Face code was NOT deleted.
Existing source components:
- tools/gen_faces.py: generates per-story per-character ID portraits via existing engine.
- kit.py: reads snapgen_data/chrome_relay.json; calls snapgen_image_gen.generate_image through Tidmunz Studio Chrome relay.
- Installed: %LOCALAPPDATA%\Tidmunz Studio\snapgen_gui_v2.py; snapgen_modules\snapgen_image_gen.py.
- studio/runner.py: face step invokes tools/gen_faces.py; cc5/build.py uses Headshot 3 from face.png.
- docs/FACE_GUIDE.md provides ID portrait technical constraints.

Preflight: story JSON characters MUST be a keyed dictionary with a face object for the actor; status dictionary and valid out_dir required. Tidmunz Studio must be running. Chrome relay port/token must be configured (never log token); the configured port listening is not proof image generation works.

Generation from project root:
python tools\gen_faces.py <story_slug> <job_id>
The established engine writes into %LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\_faces and copies face.png to %LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\<job_id>\face.png.

Thai face spec: realistic, credible local identity and distinctive features without caricature, matching era, age and role. Front-facing neutral portrait, head to shoulders, mouth shut, ears/forehead visible, uniform white lighting, plain pale gray background, no jewelry, hat or glamour filters. Variants with same character age use approved source face as reference. For a specific family member, aim plausible family resemblance without face duplication.

Check actual PNG, facial suitability and age BEFORE loading it through Headshot 3. Verify generated actor face from multiple angles. A Western default CC5 base is NOT a replacement for this process.
If generator fails, diagnose script schema, Tidmunz Chrome relay, generated image, or Headshot separately and mark BLOCKED. Do not fabricate a successful face or copy full iAvatar assets.