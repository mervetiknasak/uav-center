import { describe, expect, it } from "vitest";

import {
  DEFAULT_ROLE_CATALOG,
  filterMembershipUsers,
  filterRoleCatalog,
  groupRoleCatalog,
  membershipRoleOptions,
  sameRoleSelection,
  updateRoleSelection,
  userInitials
} from "./membership";

const users = [
  {
    id: 1,
    username: "ayse.yilmaz",
    email: "ayse@example.com",
    is_active: true,
    edk_roles: ["applicant"]
  },
  {
    id: 2,
    username: "mehmet",
    email: "mehmet@example.com",
    is_active: false,
    edk_roles: []
  },
  {
    id: 3,
    username: "deniz",
    email: "deniz@example.com",
    is_active: true,
    edk_roles: ["applicant", "approver"]
  }
];

const extendedCatalog = [
  ...DEFAULT_ROLE_CATALOG,
  {
    id: "project_manager",
    name: "Proje yöneticisi",
    title: "Projeyi yönetir",
    description: "Proje ekibini ve teslimatları yönetir.",
    category: { id: "projects", label: "Projeler", description: "Proje erişimleri" }
  }
];

describe("admin membership model", () => {
  it("updates general role selections in catalog order and preserves future role ids", () => {
    expect(updateRoleSelection(["future_role", "applicant"], "approver", true)).toEqual([
      "applicant",
      "approver",
      "future_role"
    ]);
    expect(updateRoleSelection(["applicant", "approver"], "applicant", false)).toEqual([
      "approver"
    ]);
  });

  it("filters users by search, account status and scalable role states", () => {
    expect(filterMembershipUsers(users, { query: "AYSE", status: "all", role: "all" })).toEqual([
      users[0]
    ]);
    expect(filterMembershipUsers(users, { status: "inactive", role: "unassigned" })).toEqual([
      users[1]
    ]);
    expect(filterMembershipUsers(users, { status: "active", role: "assigned" })).toEqual([
      users[0],
      users[2]
    ]);
    expect(filterMembershipUsers(users, { status: "all", role: "approver" })).toEqual([users[2]]);
  });

  it("builds role filters from the supplied catalog", () => {
    expect(membershipRoleOptions(extendedCatalog)).toContainEqual({
      label: "Proje yöneticisi",
      value: "project_manager"
    });
  });

  it("searches and groups a large role catalog by metadata", () => {
    expect(filterRoleCatalog(extendedCatalog, "projeler").map((role) => role.id)).toEqual([
      "project_manager"
    ]);
    expect(groupRoleCatalog(extendedCatalog).map((group) => group.label)).toEqual([
      "EDK Süreci",
      "Projeler"
    ]);
  });

  it("compares selections independently from display order", () => {
    expect(sameRoleSelection(["applicant", "approver"], ["approver", "applicant"])).toBe(true);
    expect(sameRoleSelection(["applicant"], ["approver"])).toBe(false);
  });

  it("creates readable initials from usernames", () => {
    expect(userInitials("ayse.yilmaz")).toBe("AY");
    expect(userInitials("mehmet")).toBe("M");
  });
});
