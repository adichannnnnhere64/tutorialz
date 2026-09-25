//! The published web app does not include the study content or navigation.
#[cfg(not(any(target_os = "android", feature = "study-preview")))]
use dioxus::prelude::*;
pub const AVAILABLE: bool = cfg!(any(target_os = "android", feature = "study-preview"));

#[cfg(any(target_os = "android", feature = "study-preview"))]
mod reader;
#[cfg(any(target_os = "android", feature = "study-preview"))]
pub use reader::Study;
#[cfg(any(target_os = "android", feature = "study-preview"))]
pub const CSS: &str = include_str!("../study/style.css");

#[cfg(not(any(target_os = "android", feature = "study-preview")))]
pub const CSS: &str = "";
#[cfg(not(any(target_os = "android", feature = "study-preview")))]
#[component]
pub fn Study() -> Element {
    rsx! {}
}
