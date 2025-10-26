document.addEventListener("DOMContentLoaded", () => {
  const bgImages = [
    "crop_fields_nir.jpg",
    "crop_fields.jpg",
    "ocean_land.jpg",
    "river_town.jpg",
    "yk_delta.jpg"
  ];

  const hero = document.querySelector(".dynamic-bg");
  if (!hero || !bgImages.length) {
    return;
  }

  const randomImage = bgImages[Math.floor(Math.random() * bgImages.length)];
  const image = new Image();
  const imagePath = `/data/backgroundimages/${randomImage}`;
  image.src = imagePath;

  const applyBackground = () => {
    hero.style.backgroundImage = `url('${imagePath}')`;
    hero.style.backgroundPosition = "center";
    hero.style.backgroundSize = "cover";
    hero.style.backgroundRepeat = "no-repeat";
    hero.classList.add("hero-image-ready");
  };

  if (image.complete) {
    applyBackground();
  } else {
    image.addEventListener("load", applyBackground);
    image.addEventListener("error", () => {
      console.error(`Failed to load hero background ${imagePath}`);
    });
  }
});
