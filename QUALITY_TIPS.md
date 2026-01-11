# Quality Improvement Tips for ThreeDLLM

## Understanding Quality Settings

### Quality Presets

ThreeDLLM offers three quality presets:

1. **Fast** (64 steps, 15.0 guidance)
   - Generation time: ~2 minutes (CPU) / ~30 seconds (GPU)
   - Best for: Quick previews, testing prompts
   - Quality: Basic

2. **Balanced** (100 steps, 17.5 guidance) - **Recommended**
   - Generation time: ~3-4 minutes (CPU) / ~1 minute (GPU)
   - Best for: Most use cases
   - Quality: Good balance of quality and speed

3. **High Quality** (128 steps, 20.0 guidance)
   - Generation time: ~5-6 minutes (CPU) / ~2 minutes (GPU)
   - Best for: Final renders, detailed objects
   - Quality: Best available

### Parameters Explained

**Karras Steps:**
- More steps = better quality but slower
- Range: 64-256
- Recommended: 100-128 for good quality
- Each step refines the 3D shape

**Guidance Scale:**
- Higher = more adherence to prompt
- Range: 1-50
- Recommended: 15-20
- Too high (>25) can cause artifacts
- Too low (<10) may ignore prompt details

## Tips for Better Quality

### 1. Use VLM Enhancement
Always enable VLM enhancement for better prompts:
- VLM expands simple prompts into detailed descriptions
- Better prompts = better 3D generation
- Example: "dragon" → "detailed dragon with scales, wings, horns, and textured surface"

### 2. Write Better Prompts
Be specific about:
- **Shape**: "round", "angular", "curved", "geometric"
- **Details**: "with intricate patterns", "smooth surface", "textured"
- **Material**: "metallic", "wooden", "ceramic", "glossy"
- **Size**: "small", "large", "compact"

**Good prompts:**
- "A detailed red dragon with textured scales, large wings, sharp horns, and a long tail"
- "A smooth, glossy ceramic vase with intricate geometric patterns"
- "A metallic futuristic car with angular edges and smooth curves"

**Poor prompts:**
- "dragon" (too vague)
- "something cool" (not descriptive)
- "a thing" (no details)

### 3. Use Image Input
Uploading a reference image helps:
- VLM analyzes the image and creates a detailed prompt
- Better understanding of shape and details
- Especially useful for complex objects

### 4. Adjust for Your Use Case

**For 3D Printing:**
- Use "High Quality" preset
- Ensure mesh has proper topology
- Check for non-manifold edges

**For Games/Real-time:**
- "Balanced" preset is usually sufficient
- Can reduce steps to 80-100 if needed
- Export as OBJ or PLY

**For Visualization:**
- Use "High Quality" preset
- Higher guidance scale (18-20)
- More steps (128-150)

### 5. Post-Processing
After generation, you can:
- Import into Blender/Maya for refinement
- Smooth the mesh
- Add details manually
- Optimize topology

### 6. Hardware Considerations

**CPU Generation:**
- Slower but works on any machine
- Use "Fast" or "Balanced" presets
- Expect 2-5 minutes per generation

**GPU Generation:**
- Much faster (5-10x speedup)
- Can use "High Quality" preset comfortably
- Expect 30 seconds - 2 minutes per generation

## Troubleshooting Poor Quality

### Issue: Blurry or Low Detail
**Solutions:**
- Increase steps to 128-150
- Increase guidance scale to 18-20
- Use more detailed prompts
- Enable VLM enhancement

### Issue: Doesn't Match Prompt
**Solutions:**
- Increase guidance scale (try 18-20)
- Write more specific prompts
- Use VLM enhancement
- Try different seed values

### Issue: Artifacts or Distortions
**Solutions:**
- Reduce guidance scale (try 15-17)
- Increase steps slightly
- Try different seed
- Simplify the prompt

### Issue: Too Slow
**Solutions:**
- Use "Fast" preset
- Reduce steps to 64-80
- Use GPU if available
- Lower guidance scale slightly

## Advanced Tips

### Seed Selection
- Same seed + same prompt = same result
- Try different seeds to get variations
- Useful for finding best result

### Batch Generation
- Generate multiple variations
- Compare results
- Select best one for refinement

### Prompt Engineering
- Start simple, add details incrementally
- Test what works for your use case
- Keep a library of good prompts

## Example Workflow

1. **Start with "Fast" preset** to test your prompt
2. **Refine prompt** based on results
3. **Use "Balanced" preset** for better quality
4. **Use "High Quality" preset** for final version
5. **Post-process** in 3D software if needed

## Best Practices

✅ **Do:**
- Use VLM enhancement
- Be specific in prompts
- Use appropriate quality preset
- Test with fast preset first
- Use GPU if available

❌ **Don't:**
- Use extremely high guidance (>25)
- Use too many steps (>200) - diminishing returns
- Use vague prompts
- Skip VLM enhancement
- Expect perfection on first try
