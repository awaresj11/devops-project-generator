import { ProjectConfig } from "./types";

export interface ProjectGeneration {
  id: string;
  timestamp: number;
  config: ProjectConfig;
  generationTime?: number; // seconds
  success?: boolean;
  error?: string;
}

export interface UserSession {
  id: string;
  startTime: number;
  endTime?: number;
  projectCount: number;
  interactions: number;
}

export interface AnalyticsData {
  totalProjects: number;
  generations: ProjectGeneration[];
  sessions: UserSession[];
  lastUpdated: number;
  performanceMetrics: {
    avgGenerationTime: number;
    errorRate: number;
    popularTimeOfDay: string;
    peakDay: string;
  };
  userMetrics: {
    returningUsers: number;
    avgProjectsPerUser: number;
    mostActiveDay: string;
    userSatisfaction: number;
  };
}

const STORAGE_KEY = "devops-generator-analytics";

export function getAnalyticsData(): AnalyticsData {
  if (typeof window === "undefined") {
    return {
      totalProjects: 0,
      generations: [],
      sessions: [],
      lastUpdated: Date.now(),
      performanceMetrics: {
        avgGenerationTime: 0,
        errorRate: 0,
        popularTimeOfDay: "N/A",
        peakDay: "N/A",
      },
      userMetrics: {
        returningUsers: 0,
        avgProjectsPerUser: 0,
        mostActiveDay: "N/A",
        userSatisfaction: 0,
      },
    };
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      // Ensure new fields exist for backward compatibility
      return {
        ...data,
        sessions: data.sessions || [],
        performanceMetrics: data.performanceMetrics || {
          avgGenerationTime: 0,
          errorRate: 0,
          popularTimeOfDay: "N/A",
          peakDay: "N/A",
        },
        userMetrics: data.userMetrics || {
          returningUsers: 0,
          avgProjectsPerUser: 0,
          mostActiveDay: "N/A",
          userSatisfaction: 0,
        },
      };
    }
  } catch (error) {
    console.error("Failed to load analytics data:", error);
  }

  return {
    totalProjects: 0,
    generations: [],
    sessions: [],
    lastUpdated: Date.now(),
    performanceMetrics: {
      avgGenerationTime: 0,
      errorRate: 0,
      popularTimeOfDay: "N/A",
      peakDay: "N/A",
    },
    userMetrics: {
      returningUsers: 0,
      avgProjectsPerUser: 0,
      mostActiveDay: "N/A",
      userSatisfaction: 0,
    },
  };
}

export function saveAnalyticsData(data: AnalyticsData): void {
  if (typeof window === "undefined") return;

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error("Failed to save analytics data:", error);
  }
}

export function trackProjectGeneration(config: ProjectConfig, generationTime?: number, success?: boolean, error?: string): void {
  const data = getAnalyticsData();
  
  const generation: ProjectGeneration = {
    id: `gen-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: Date.now(),
    config,
    generationTime,
    success: success !== false, // Default to true unless explicitly false
    error,
  };

  data.generations.push(generation);
  data.totalProjects += 1;
  data.lastUpdated = Date.now();

  // Update performance metrics
  if (generationTime) {
    const successfulGenerations = data.generations.filter(g => g.success !== false && g.generationTime);
    const avgTime = successfulGenerations.length > 0 
      ? successfulGenerations.reduce((sum, g) => sum + (g.generationTime || 0), 0) / successfulGenerations.length
      : 0;
    data.performanceMetrics.avgGenerationTime = avgTime;
  }

  // Update error rate
  const errorCount = data.generations.filter(g => g.success === false).length;
  data.performanceMetrics.errorRate = data.generations.length > 0 ? (errorCount / data.generations.length) * 100 : 0;

  // Keep only last 1000 generations to avoid storage issues
  if (data.generations.length > 1000) {
    data.generations = data.generations.slice(-1000);
  }

  // Update user metrics
  updateUserMetrics(data);

  saveAnalyticsData(data);
}

export function trackUserSession(): void {
  const data = getAnalyticsData();
  
  const session: UserSession = {
    id: `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    startTime: Date.now(),
    projectCount: 0,
    interactions: 1,
  };

  data.sessions.push(session);

  // Keep only last 500 sessions
  if (data.sessions.length > 500) {
    data.sessions = data.sessions.slice(-500);
  }

  saveAnalyticsData(data);
}

export function trackInteraction(): void {
  const data = getAnalyticsData();
  
  if (data.sessions.length > 0) {
    const currentSession = data.sessions[data.sessions.length - 1];
    currentSession.interactions += 1;
    currentSession.endTime = Date.now();
  }

  saveAnalyticsData(data);
}

export function trackProjectInSession(): void {
  const data = getAnalyticsData();
  
  if (data.sessions.length > 0) {
    const currentSession = data.sessions[data.sessions.length - 1];
    currentSession.projectCount += 1;
    currentSession.endTime = Date.now();
  }

  saveAnalyticsData(data);
}

function updateUserMetrics(data: AnalyticsData): void {
  const sessions = data.sessions;
  if (sessions.length === 0) return;

  // Calculate returning users (sessions with more than 1 project)
  const returningUsers = sessions.filter(s => s.projectCount > 1).length;
  data.userMetrics.returningUsers = returningUsers;

  // Calculate average projects per user
  const totalProjects = sessions.reduce((sum, s) => sum + s.projectCount, 0);
  data.userMetrics.avgProjectsPerUser = sessions.length > 0 ? totalProjects / sessions.length : 0;

  // Calculate most active day
  const dayCounts: Record<string, number> = {};
  sessions.forEach(session => {
    const day = new Date(session.startTime).toLocaleDateString('en-US', { weekday: 'long' });
    dayCounts[day] = (dayCounts[day] || 0) + 1;
  });
  
  const mostActiveDay = Object.entries(dayCounts).sort(([, a], [, b]) => b - a)[0]?.[0] || "N/A";
  data.userMetrics.mostActiveDay = mostActiveDay;

  // Calculate user satisfaction (simulated based on success rate and session duration)
  const avgSessionDuration = sessions.reduce((sum, s) => {
    const duration = (s.endTime || Date.now()) - s.startTime;
    return sum + duration;
  }, 0) / sessions.length;
  
  // Simulate satisfaction based on success rate and engagement
  const successRate = 100 - data.performanceMetrics.errorRate;
  const engagementScore = Math.min(100, (data.userMetrics.avgProjectsPerUser * 20) + (avgSessionDuration / 60000 * 20)); // 20 points per project, 20 points per minute
  data.userMetrics.userSatisfaction = Math.round((successRate * 0.6 + engagementScore * 0.4) * 5) / 100; // Convert to 5-point scale
}

export function calculateTechnologyStats(generations: ProjectGeneration[]) {
  const stats = {
    ci: {} as Record<string, number>,
    infra: {} as Record<string, number>,
    deploy: {} as Record<string, number>,
    observability: {} as Record<string, number>,
    security: {} as Record<string, number>,
  };

  generations.forEach((gen) => {
    const { config } = gen;
    
    stats.ci[config.ci] = (stats.ci[config.ci] || 0) + 1;
    stats.infra[config.infra] = (stats.infra[config.infra] || 0) + 1;
    stats.deploy[config.deploy] = (stats.deploy[config.deploy] || 0) + 1;
    stats.observability[config.observability] = (stats.observability[config.observability] || 0) + 1;
    stats.security[config.security] = (stats.security[config.security] || 0) + 1;
  });

  return stats;
}

export function getPopularCombinations(generations: ProjectGeneration[]) {
  const combinations = new Map<string, { count: number; config: ProjectConfig }>();

  generations.forEach((gen) => {
    const key = `${gen.config.infra}|${gen.config.ci}|${gen.config.deploy}`;
    const existing = combinations.get(key);
    
    if (existing) {
      existing.count += 1;
    } else {
      combinations.set(key, { count: 1, config: gen.config });
    }
  });

  return Array.from(combinations.entries())
    .map(([key, value]) => ({
      name: `${value.config.infra} + ${value.config.ci} + ${value.config.deploy}`,
      count: value.count,
      percentage: (value.count / generations.length) * 100,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

export function getTrendingTechnologies(generations: ProjectGeneration[]) {
  if (generations.length < 10) return [];

  const recentCount = Math.min(50, Math.floor(generations.length / 2));
  const recent = generations.slice(-recentCount);
  const older = generations.slice(0, -recentCount);

  const recentStats = calculateTechnologyStats(recent);
  const olderStats = calculateTechnologyStats(older);

  const trends: Array<{ technology: string; growth: number; category: string }> = [];

  // Calculate growth for each technology
  const categories = [
    { key: 'ci', name: 'ci-cd' },
    { key: 'infra', name: 'infrastructure' },
    { key: 'deploy', name: 'deployment' },
    { key: 'observability', name: 'observability' },
    { key: 'security', name: 'security' },
  ];

  categories.forEach(({ key, name }) => {
    const recentCat = recentStats[key as keyof typeof recentStats];
    const olderCat = olderStats[key as keyof typeof olderStats];

    Object.keys(recentCat).forEach((tech) => {
      const recentPercentage = (recentCat[tech] / recentCount) * 100;
      const olderPercentage = ((olderCat[tech] || 0) / older.length) * 100;
      const growth = recentPercentage - olderPercentage;

      if (growth > 0) {
        trends.push({
          technology: tech.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          growth: Math.round(growth),
          category: name,
        });
      }
    });
  });

  return trends.sort((a, b) => b.growth - a.growth).slice(0, 5);
}

export function getPerformanceMetrics() {
  const data = getAnalyticsData();
  return data.performanceMetrics;
}

export function getUserMetrics() {
  const data = getAnalyticsData();
  return data.userMetrics;
}

export function exportAnalyticsData(): string {
  const data = getAnalyticsData();
  
  const exportData = {
    summary: {
      totalProjects: data.totalProjects,
      totalSessions: data.sessions.length,
      successRate: 100 - data.performanceMetrics.errorRate,
      avgGenerationTime: data.performanceMetrics.avgGenerationTime,
      userSatisfaction: data.userMetrics.userSatisfaction,
      lastUpdated: new Date(data.lastUpdated).toISOString(),
    },
    technologyStats: calculateTechnologyStats(data.generations),
    popularCombinations: getPopularCombinations(data.generations),
    trendingTechnologies: getTrendingTechnologies(data.generations),
    performanceMetrics: data.performanceMetrics,
    userMetrics: data.userMetrics,
    recentGenerations: data.generations.slice(-10).map(g => ({
      id: g.id,
      timestamp: new Date(g.timestamp).toISOString(),
      config: g.config,
      generationTime: g.generationTime,
      success: g.success,
      error: g.error,
    })),
  };

  return JSON.stringify(exportData, null, 2);
}

export function resetAnalytics(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}
