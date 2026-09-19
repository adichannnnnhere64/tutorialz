use tutorialz_core::*;
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "content/catalog.json".into());
    let catalog: Catalog = serde_json::from_slice(&std::fs::read(&path)?)?;
    validate_catalog(&catalog)?;
    let base = std::path::Path::new(&path).parent().unwrap();
    let mut courses = vec![];
    for entry in &catalog.courses {
        let bytes = std::fs::read(base.join(&entry.path))?;
        if hash(&bytes) != entry.sha256 {
            return Err(format!("Hash mismatch: {}", entry.id).into());
        }
        let course: Course = serde_json::from_slice(&bytes)?;
        if course.id != entry.id {
            return Err("Course ID mismatch".into());
        }
        courses.push(course);
    }
    validate_courses(&courses)?;
    for id in duplicate_prompts(&courses) {
        eprintln!("Duplicate prompt: {id}");
    }
    println!("Validated {} courses", courses.len());
    Ok(())
}
