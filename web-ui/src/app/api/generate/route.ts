import { NextRequest, NextResponse } from "next/server";
import { generateProject } from "@/lib/generator";
import { ProjectConfig } from "@/lib/types";

export async function POST(request: NextRequest) {
  try {
    const config: ProjectConfig = await request.json();

    // Validate required fields
    if (!config.projectName || !config.projectName.trim()) {
      return NextResponse.json(
        { error: "Project name is required" },
        { status: 400 }
      );
    }

    // Validate project name format
    if (!/^[a-zA-Z0-9_-]+$/.test(config.projectName)) {
      return NextResponse.json(
        { error: "Project name can only contain letters, numbers, hyphens, and underscores" },
        { status: 400 }
      );
    }

    if (config.projectName.length > 50) {
      return NextResponse.json(
        { error: "Project name too long (max 50 characters)" },
        { status: 400 }
      );
    }

    const result = generateProject(config);

    return NextResponse.json(result);
  } catch (error) {
    console.error("Generation error:", error);
    return NextResponse.json(
      { error: "Failed to generate project" },
      { status: 500 }
    );
  }
}
