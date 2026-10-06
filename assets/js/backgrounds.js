document.addEventListener("DOMContentLoaded", () => {
  const bgImages = [
    "crop_fields_nir.jpg",
    "crop_fields.jpg",
    "ocean_land.jpg",
    "river_town.jpg",
    "yk_delta.jpg",
    "bridgers.jpg",
    // NASA Earth Observatory / Landsat (public domain) — see data/backgroundimages/CREDITS.md
    "mt_golden_triangle.jpg",
    "mt_glacier_np.jpg",
    "mt_beartooths.jpg",
    "wy_tetons.jpg",
    "wy_bighorn_basin.jpg"
  ];

  const hero = document.querySelector(".dynamic-bg");
  if (!hero || !bgImages.length) return;

  // Shuffle
  for (let i = bgImages.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [bgImages[i], bgImages[j]] = [bgImages[j], bgImages[i]];
  }

  let index = 0;
  const path = (name) => `/data/backgroundimages/${name}`;

  const apply = (src) => {
    hero.style.backgroundImage = `url('${src}')`;
    hero.style.backgroundPosition = "center";
    hero.style.backgroundSize = "cover";
    hero.style.backgroundRepeat = "no-repeat";
    hero.classList.add("hero-image-ready");
  };

  // Load first image
  const first = new Image();
  first.src = path(bgImages[0]);
  const show = () => apply(path(bgImages[0]));
  if (first.complete) show(); else first.addEventListener("load", show);

  // Cycle every 8s with a soft fade
  if (bgImages.length > 1) {
    setInterval(() => {
      index = (index + 1) % bgImages.length;
      const next = new Image();
      next.src = path(bgImages[index]);
      const swap = () => {
        hero.style.transition = "background-image 0s";
        hero.classList.remove("hero-image-ready");
        setTimeout(() => {
          apply(path(bgImages[index]));
          hero.classList.add("hero-image-ready");
        }, 400);
      };
      if (next.complete) swap(); else next.addEventListener("load", swap);
    }, 8000);
  }
});
