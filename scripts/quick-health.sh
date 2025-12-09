#!/bin/bash
# Quick health check for VulcanLab services

echo "Quick Health Check"
echo "=================="

# Check supervisord services
supervisorctl status | grep -E "postgresql|backend|frontend"

echo ""
echo "Backend API:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
echo ""

echo ""
echo "Frontend:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
echo ""
